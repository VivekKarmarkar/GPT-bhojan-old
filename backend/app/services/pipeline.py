import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models.schemas import (
    AnalyzeResponse,
    DetectionResult,
    FoodAnalysis,
    SegmentationResult,
    SegmentedFoodItem,
)
from app.services.detection import detect_with_yolo_world
from app.services.gpt_service import analyze_food_image, classify_food_crop
from app.services.image_store import save_crop, save_visualization
from app.services.nms import cross_class_nms
from app.services.post_processing import run_post_processing
from app.services.segmentation import build_visualization, segment_all_crops
from app.utils.image import (
    bytes_to_numpy_rgb,
    numpy_rgb_to_jpeg_bytes,
    resize_if_needed,
)
from app.utils.parsing import extract_item_names

logger = logging.getLogger(__name__)


def _crop_box(img_arr, bbox: list[float]) -> tuple[bytes, tuple[int, int, int, int]]:
    """Crop a bounding box region from the image array, return JPEG bytes and int bbox."""
    h, w = img_arr.shape[:2]
    x1 = max(0, int(bbox[0]))
    y1 = max(0, int(bbox[1]))
    x2 = min(w, int(bbox[2]))
    y2 = min(h, int(bbox[3]))
    crop_arr = img_arr[y1:y2, x1:x2]
    return numpy_rgb_to_jpeg_bytes(crop_arr), (x1, y1, x2, y2)


def run_pipeline(image_bytes: bytes) -> AnalyzeResponse:
    timing: dict[str, float | str] = {}

    # Resize large images to keep latency down
    image_bytes = resize_if_needed(image_bytes, max_dim=2048)
    img_arr = bytes_to_numpy_rgb(image_bytes)
    img_h, img_w = img_arr.shape[:2]

    # ── Step 1: GPT-4o Vision Analysis ──────────────────────────
    t0 = time.time()
    parsed, _raw = analyze_food_image(image_bytes)
    timing["gpt_vision_s"] = round(time.time() - t0, 2)

    analysis = FoodAnalysis(**parsed)
    item_names = extract_item_names(parsed.get("items", ""))
    if not item_names:
        item_names = ["food"]

    # ── Step 2: YOLO-World-XL Detection ─────────────────────────
    t1 = time.time()
    yolo_boxes = detect_with_yolo_world(image_bytes, class_names=item_names)
    timing["yolo_detection_s"] = round(time.time() - t1, 2)

    if not yolo_boxes:
        # No detections — return GPT-only result
        timing["total_s"] = round(
            sum(v for v in timing.values() if isinstance(v, float)), 2
        )
        return AnalyzeResponse(
            analysis=analysis,
            detections=DetectionResult(detections=[]),
            segmentation=SegmentationResult(),
            timing=timing,
        )

    # ── Step 3: Cross-class IoU NMS ─────────────────────────────
    t2 = time.time()
    box_dicts = [
        {"bbox": b.bbox, "label": b.label, "confidence": b.confidence}
        for b in yolo_boxes
    ]
    try:
        filtered_boxes = cross_class_nms(box_dicts, iou_threshold=0.5)
    except Exception as exc:
        logger.error("NMS failed, using unfiltered boxes: %s", exc)
        filtered_boxes = box_dicts
    timing["nms_s"] = round(time.time() - t2, 2)

    # ── Step 4: GPT per-box classification (parallel) ───────────
    t3 = time.time()
    description = parsed.get("description", "")
    confirmed_items: list[dict] = []

    def _classify_one(box_dict: dict) -> dict | None:
        crop_bytes, int_bbox = _crop_box(img_arr, box_dict["bbox"])
        label = classify_food_crop(crop_bytes, description)
        if label is None:
            return None
        return {
            "crop_bytes": crop_bytes,
            "label": label,
            "bbox": int_bbox,
            "confidence": box_dict["confidence"],
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_classify_one, box): box["label"]
            for box in filtered_boxes
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    confirmed_items.append(result)
            except Exception:
                pass
    timing["gpt_classification_s"] = round(time.time() - t3, 2)

    if not confirmed_items:
        timing["total_s"] = round(
            sum(v for v in timing.values() if isinstance(v, float)), 2
        )
        return AnalyzeResponse(
            analysis=analysis,
            detections=DetectionResult(detections=[]),
            segmentation=SegmentationResult(),
            timing=timing,
        )

    # ── Step 5: Crop → lang-SAM segmentation (parallel) ────────
    t4 = time.time()
    seg_result = SegmentationResult()
    try:
        seg_items_data = segment_all_crops(
            image_bytes, confirmed_items, (img_h, img_w)
        )
    except Exception as exc:
        logger.error("Segmentation failed: %s", exc)
        timing["segmentation_error"] = str(exc)
        seg_items_data = []
    timing["segmentation_s"] = round(time.time() - t4, 2)

    # ── Step 5.5: Post-processing filters ────────────────────
    if seg_items_data:
        t_pp = time.time()
        seg_items_data, pp_stats = run_post_processing(seg_items_data)
        timing["post_processing_s"] = round(time.time() - t_pp, 2)
        for k, v in pp_stats.items():
            timing[f"pp_{k}"] = v

    try:
        if seg_items_data:
            vis_bytes = build_visualization(image_bytes, seg_items_data)
            vis_url = save_visualization(vis_bytes)
            seg_items = []
            for item in seg_items_data:
                crop_url = save_crop(item.crop_bytes, item.label)
                seg_items.append(
                    SegmentedFoodItem(
                        label=item.label,
                        crop_url=crop_url,
                        confidence=item.confidence,
                    )
                )
            seg_result = SegmentationResult(
                segmented_items=seg_items,
                visualization_url=vis_url,
                item_count=len(seg_items),
            )
    except Exception as exc:
        logger.error("Visualization/save failed: %s", exc)

    timing["total_s"] = round(
        sum(v for v in timing.values() if isinstance(v, float)), 2
    )

    return AnalyzeResponse(
        analysis=analysis,
        detections=DetectionResult(detections=[]),
        segmentation=seg_result,
        timing=timing,
    )
