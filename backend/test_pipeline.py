"""End-to-end pipeline test — YOLO-World + Crop-to-SAM.

Usage:
    cd backend/
    python test_pipeline.py [path/to/image.jpg]

If no image path is given, it looks for any .jpg/.png in ../test_images/.
"""

import os
import sys
import time
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings  # noqa: E402
from app.services.detection import detect_with_yolo_world  # noqa: E402
from app.services.gpt_service import analyze_food_image, classify_food_crop  # noqa: E402
from app.services.nms import cross_class_nms  # noqa: E402
from app.services.segmentation import (  # noqa: E402
    build_visualization,
    segment_all_crops,
)
from app.services.post_processing import run_post_processing  # noqa: E402
from app.services.image_store import save_visualization, save_crop  # noqa: E402
from app.utils.image import (  # noqa: E402
    bytes_to_numpy_rgb,
    numpy_rgb_to_jpeg_bytes,
    resize_if_needed,
)
from app.utils.parsing import extract_item_names  # noqa: E402


def find_test_image() -> Path | None:
    test_dir = Path(__file__).resolve().parent.parent / "test_images"
    if test_dir.is_dir():
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            files = list(test_dir.glob(ext))
            if files:
                return files[0]
    return None


def main():
    # Determine image path
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        img_path = find_test_image()

    if img_path is None or not img_path.exists():
        print("No test image found. Provide a path as argument or place images in ../test_images/")
        sys.exit(1)

    print(f"Test image: {img_path}")
    image_bytes = img_path.read_bytes()
    image_bytes = resize_if_needed(image_bytes)
    img_arr = bytes_to_numpy_rgb(image_bytes)
    img_h, img_w = img_arr.shape[:2]
    print(f"Image size: {len(image_bytes):,} bytes ({img_w}x{img_h})")

    # --- Step 1: GPT-4o Vision ---
    print("\n=== Step 1: GPT-4o Vision Analysis ===")
    t0 = time.time()
    parsed, raw_text = analyze_food_image(image_bytes)
    gpt_time = time.time() - t0
    print(f"Time: {gpt_time:.2f}s")
    for key, val in parsed.items():
        preview = val[:120].replace("\n", " ") + ("..." if len(val) > 120 else "")
        print(f"  {key}: {preview}")

    item_names = extract_item_names(parsed.get("items", ""))
    if not item_names:
        item_names = ["food"]
    print(f"\nExtracted items: {item_names}")

    # --- Step 2: YOLO-World-XL Detection ---
    print("\n=== Step 2: YOLO-World-XL Detection ===")
    t1 = time.time()
    yolo_boxes = detect_with_yolo_world(image_bytes, class_names=item_names)
    yolo_time = time.time() - t1
    print(f"Time: {yolo_time:.2f}s")
    print(f"Detections: {len(yolo_boxes)}")
    for box in yolo_boxes:
        print(f"  [{box.label}] conf={box.confidence:.2f} bbox={box.bbox}")

    if not yolo_boxes:
        print("\nNo YOLO detections — pipeline would return GPT-only result.")
        total = gpt_time + yolo_time
        print(f"\n=== Timing Summary ===")
        print(f"  GPT-4o Vision:   {gpt_time:.2f}s")
        print(f"  YOLO-World:      {yolo_time:.2f}s")
        print(f"  Total:           {total:.2f}s")
        return

    # --- Step 3: Cross-class NMS ---
    print("\n=== Step 3: Cross-class IoU NMS ===")
    t2 = time.time()
    box_dicts = [
        {"bbox": b.bbox, "label": b.label, "confidence": b.confidence}
        for b in yolo_boxes
    ]
    filtered = cross_class_nms(box_dicts, iou_threshold=0.5)
    nms_time = time.time() - t2
    print(f"Time: {nms_time:.4f}s")
    print(f"Before NMS: {len(box_dicts)} → After NMS: {len(filtered)}")

    # --- Step 4: GPT per-box classification ---
    print("\n=== Step 4: GPT Per-box Classification ===")
    t3 = time.time()
    description = parsed.get("description", "")
    confirmed_items = []
    for i, box in enumerate(filtered):
        x1 = max(0, int(box["bbox"][0]))
        y1 = max(0, int(box["bbox"][1]))
        x2 = min(img_w, int(box["bbox"][2]))
        y2 = min(img_h, int(box["bbox"][3]))
        crop_arr = img_arr[y1:y2, x1:x2]
        crop_bytes = numpy_rgb_to_jpeg_bytes(crop_arr)

        label = classify_food_crop(crop_bytes, description)
        status = f"→ {label}" if label else "→ REJECTED"
        print(f"  Box {i} [{box['label']}]: {status}")

        if label is not None:
            confirmed_items.append({
                "crop_bytes": crop_bytes,
                "label": label,
                "bbox": (x1, y1, x2, y2),
                "confidence": box["confidence"],
            })
    classify_time = time.time() - t3
    print(f"Time: {classify_time:.2f}s")
    print(f"Confirmed: {len(confirmed_items)} / {len(filtered)}")

    if not confirmed_items:
        print("\nNo confirmed items — pipeline would return GPT-only result.")
        return

    # --- Step 5: Crop → lang-SAM Segmentation ---
    print("\n=== Step 5: Crop → lang-SAM Segmentation ===")
    t4 = time.time()
    seg_items = segment_all_crops(image_bytes, confirmed_items, (img_h, img_w))
    seg_time = time.time() - t4
    print(f"Time: {seg_time:.2f}s")
    print(f"Segmented: {len(seg_items)} items")
    for item in seg_items:
        mask_pixels = item.mask.sum()
        print(f"  [{item.label}] mask_pixels={mask_pixels:,} crop_size={len(item.crop_bytes):,}B")

    # --- Step 5.5: Post-Processing Filters ---
    print("\n=== Step 5.5: Post-Processing Filters ===")
    t_pp = time.time()
    before_count = len(seg_items)
    seg_items, pp_stats = run_post_processing(seg_items, enable_gpt_quality_check=True)
    pp_time = time.time() - t_pp
    print(f"Time: {pp_time:.2f}s")
    print(f"Before: {before_count} → After: {len(seg_items)}")
    for key, val in pp_stats.items():
        print(f"  {key}: {val}")

    # --- Step 6: Visualization + Save ---
    print("\n=== Step 6: Visualization + Save ===")
    t5 = time.time()
    if seg_items:
        vis_bytes = build_visualization(image_bytes, seg_items)
        vis_url = save_visualization(vis_bytes)
        print(f"Visualization: {vis_url}")
        for item in seg_items:
            crop_url = save_crop(item.crop_bytes, item.label)
            print(f"  Crop [{item.label}]: {crop_url}")
    save_time = time.time() - t5
    print(f"Time: {save_time:.2f}s")

    # --- Timing Summary ---
    total = gpt_time + yolo_time + nms_time + classify_time + seg_time + pp_time + save_time
    print(f"\n=== Timing Summary ===")
    print(f"  GPT-4o Vision:      {gpt_time:.2f}s")
    print(f"  YOLO-World:         {yolo_time:.2f}s")
    print(f"  NMS:                {nms_time:.4f}s")
    print(f"  GPT Classification: {classify_time:.2f}s")
    print(f"  Segmentation:       {seg_time:.2f}s")
    print(f"  Post-Processing:    {pp_time:.2f}s")
    print(f"  Save:               {save_time:.2f}s")
    print(f"  Total:              {total:.2f}s")


if __name__ == "__main__":
    main()
