import io
import json
import logging
import os
from dataclasses import dataclass

import replicate

from app.config import settings

logger = logging.getLogger(__name__)

YOLO_WORLD_MODEL = (
    "franz-biz/yolo-world-xl:"
    "fd1305d3fc19e81540542f51c2530cf8f393e28cc6ff4976337c3e2b75c7c292"
)


@dataclass
class YoloBox:
    bbox: list[float]    # [x1, y1, x2, y2] pixels
    label: str
    confidence: float


def detect_with_yolo_world(
    image_bytes: bytes,
    class_names: list[str],
    score_thr: float = 0.05,
    nms_thr: float = 0.5,
    max_num_boxes: int = 20,
) -> list[YoloBox]:
    """Detect food items using YOLO-World-XL on Replicate."""
    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token

    try:
        output = replicate.run(
            YOLO_WORLD_MODEL,
            input={
                "input_media": io.BytesIO(image_bytes),
                "class_names": ", ".join(class_names),
                "score_thr": score_thr,
                "nms_thr": nms_thr,
                "max_num_boxes": max_num_boxes,
                "return_json": True,
            },
        )
    except Exception as exc:
        logger.error("YOLO-World detection failed: %s", exc)
        return []

    return _parse_yolo_output(output)


def _parse_yolo_output(output) -> list[YoloBox]:
    """Parse YOLO-World JSON output.

    Actual output format from Replicate:
        {"json_str": '{"Det-0": {"x0": .., "y0": .., "x1": .., "y1": .., "score": .., "cls": ".."}, ...}',
         "media_path": ...}

    json_str is a JSON *string* containing a dict of detection dicts keyed "Det-0", "Det-1", etc.
    Each detection has: x0, y0, x1, y1, score, cls.
    """
    boxes: list[YoloBox] = []

    if not isinstance(output, dict):
        logger.warning("YOLO output is not a dict: %s", type(output))
        return boxes

    json_str = output.get("json_str")
    if not json_str:
        logger.warning("YOLO output has no json_str")
        return boxes

    try:
        detections = json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse YOLO json_str: %s", exc)
        return boxes

    # detections is a dict: {"Det-0": {...}, "Det-1": {...}, ...}
    for det_key, det in detections.items():
        if not isinstance(det, dict):
            continue

        try:
            bbox = [float(det["x0"]), float(det["y0"]), float(det["x1"]), float(det["y1"])]
            label = str(det["cls"])
            confidence = float(det["score"])
            boxes.append(YoloBox(bbox=bbox, label=label, confidence=confidence))
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Skipping detection %s: %s", det_key, exc)

    return boxes


def check_replicate_token() -> bool:
    """Verify Replicate API token is valid."""
    try:
        os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token
        client = replicate.Client(api_token=settings.replicate_api_token)
        # Use just the model name (without version hash) for the check
        client.models.get("franz-biz/yolo-world-xl")
        return True
    except Exception:
        return False
