import numpy as np


def compute_iou(box_a: list[float], box_b: list[float]) -> float:
    """IoU between two [x1, y1, x2, y2] boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def cross_class_nms(
    boxes: list[dict],  # each: {"bbox": [x1,y1,x2,y2], "label": str, "confidence": float}
    iou_threshold: float = 0.5,
) -> list[dict]:
    """Greedy NMS: sort by confidence desc, suppress if IoU > threshold."""
    if not boxes:
        return []

    sorted_boxes = sorted(boxes, key=lambda b: b["confidence"], reverse=True)
    kept: list[dict] = []

    for box in sorted_boxes:
        should_keep = True
        for kept_box in kept:
            if compute_iou(box["bbox"], kept_box["bbox"]) > iou_threshold:
                should_keep = False
                break
        if should_keep:
            kept.append(box)

    return kept
