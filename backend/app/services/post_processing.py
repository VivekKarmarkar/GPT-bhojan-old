"""Post-processing filters for segmented food items.

Runs AFTER segmentation, BEFORE visualization. Ordered cheapest-first:
  1. Brightness filter  — reject mostly-black crops  (local, <10ms)
  2. Duplicate merge     — keep largest mask per label (local, <1ms)
  3. Containment resolve — GPT picks inner vs outer   (GPT text, ~0.5s/pair)
  4. GPT quality check   — verify crop matches label  (GPT vision, parallel)
"""

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image

from app.services.segmentation import SegmentedItem
from app.utils.image import image_bytes_to_data_uri

logger = logging.getLogger(__name__)

# ── Filter 1: Brightness ────────────────────────────────────────────

BRIGHTNESS_THRESHOLD = 30
MIN_BRIGHT_PIXELS = 100


def _passes_brightness(item: SegmentedItem) -> bool:
    """Reject crops that are mostly black (failed segmentation).

    Replicates v12 logic: convert to grayscale, count pixels > 30,
    reject if count <= 100.
    """
    try:
        img = Image.open(io.BytesIO(item.crop_bytes)).convert("L")
        arr = np.array(img)
        bright_count = int((arr > BRIGHTNESS_THRESHOLD).sum())
        return bright_count > MIN_BRIGHT_PIXELS
    except Exception as exc:
        logger.warning("Brightness filter error for '%s': %s — keeping item", item.label, exc)
        return True  # fail-open


def filter_brightness(items: list[SegmentedItem]) -> tuple[list[SegmentedItem], int]:
    kept = [item for item in items if _passes_brightness(item)]
    removed = len(items) - len(kept)
    if removed:
        logger.info("Brightness filter removed %d items", removed)
    return kept, removed


# ── Filter 2: Duplicate Label Merge ─────────────────────────────────


def filter_duplicates(items: list[SegmentedItem]) -> tuple[list[SegmentedItem], int]:
    """Keep only the largest mask per normalized label."""
    groups: dict[str, list[SegmentedItem]] = {}
    for item in items:
        key = item.label.strip().lower()
        groups.setdefault(key, []).append(item)

    kept: list[SegmentedItem] = []
    for group in groups.values():
        if len(group) == 1:
            kept.append(group[0])
        else:
            best = max(group, key=lambda it: it.mask.sum())
            kept.append(best)

    removed = len(items) - len(kept)
    if removed:
        logger.info("Duplicate merge removed %d items", removed)
    return kept, removed


# ── Filter 3: Containment Resolution ────────────────────────────────

CONTAINMENT_RATIO = 0.8


def _bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    """Derive (x1, y1, x2, y2) bounding box from a boolean mask."""
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def _box_area(box: tuple[int, int, int, int]) -> int:
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0, x2 - x1) * max(0, y2 - y1)


def _ask_gpt_containment(inner_label: str, outer_label: str) -> str | None:
    """Ask GPT which label to keep when one contains the other.

    Returns the label to KEEP, or None on failure (keep both).
    """
    try:
        from app.services.gpt_service import _get_client

        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"I detected '{inner_label}' inside '{outer_label}' in a food photo. "
                        "Which is more useful to show the user as a separate food item? "
                        "Reply with just the label to KEEP."
                    ),
                }
            ],
            max_tokens=30,
        )
        answer = response.choices[0].message.content.strip().strip("'\"").lower()
        # Match against our labels
        if inner_label.strip().lower() in answer:
            return inner_label
        if outer_label.strip().lower() in answer:
            return outer_label
        return None  # unexpected answer — keep both
    except Exception as exc:
        logger.warning("Containment GPT call failed: %s — keeping both", exc)
        return None


def filter_containment(items: list[SegmentedItem]) -> tuple[list[SegmentedItem], int]:
    """Remove items where one bounding box is 80%+ inside another."""
    if len(items) < 2:
        return items, 0

    bboxes = [_bbox_from_mask(item.mask) for item in items]
    to_remove: set[int] = set()

    for i in range(len(items)):
        if i in to_remove:
            continue
        for j in range(i + 1, len(items)):
            if j in to_remove:
                continue
            # Skip same-label pairs (already handled by duplicate merge)
            if items[i].label.strip().lower() == items[j].label.strip().lower():
                continue

            inter = _intersection_area(bboxes[i], bboxes[j])
            area_i = _box_area(bboxes[i])
            area_j = _box_area(bboxes[j])
            smaller_area = min(area_i, area_j) if min(area_i, area_j) > 0 else 1

            ratio = inter / smaller_area
            if ratio > CONTAINMENT_RATIO:
                # Determine inner/outer by area
                if area_i < area_j:
                    inner_idx, outer_idx = i, j
                else:
                    inner_idx, outer_idx = j, i

                keep_label = _ask_gpt_containment(
                    items[inner_idx].label, items[outer_idx].label
                )
                if keep_label is not None:
                    # Remove the one GPT says to drop
                    if keep_label.strip().lower() == items[inner_idx].label.strip().lower():
                        to_remove.add(outer_idx)
                    else:
                        to_remove.add(inner_idx)

    kept = [item for idx, item in enumerate(items) if idx not in to_remove]
    removed = len(to_remove)
    if removed:
        logger.info("Containment filter removed %d items", removed)
    return kept, removed


# ── Filter 4: GPT Mask Quality Check ────────────────────────────────


def _check_crop_quality(item: SegmentedItem) -> bool:
    """Ask GPT-4o if the crop clearly shows the labeled food. Returns True to keep."""
    try:
        from app.services.gpt_service import _get_client

        client = _get_client()
        data_uri = image_bytes_to_data_uri(item.crop_bytes)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Does this image clearly show {item.label}? "
                                "Reply 'yes' or 'no'."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=10,
        )
        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer
    except Exception as exc:
        logger.warning("GPT quality check failed for '%s': %s — keeping item", item.label, exc)
        return True  # fail-open


def filter_gpt_quality(items: list[SegmentedItem]) -> tuple[list[SegmentedItem], int]:
    """Parallel GPT vision check — remove items that don't match their label."""
    kept: list[SegmentedItem] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_check_crop_quality, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                if future.result():
                    kept.append(item)
                else:
                    logger.info("GPT quality check rejected '%s'", item.label)
            except Exception as exc:
                logger.warning("GPT quality future error for '%s': %s — keeping", item.label, exc)
                kept.append(item)

    removed = len(items) - len(kept)
    return kept, removed


# ── Orchestrator ─────────────────────────────────────────────────────


def run_post_processing(
    items: list[SegmentedItem],
    enable_gpt_quality_check: bool = True,
) -> tuple[list[SegmentedItem], dict[str, int]]:
    """Run all post-processing filters in order. Returns (filtered_items, stats)."""
    stats: dict[str, int] = {
        "input_count": len(items),
        "brightness_removed": 0,
        "duplicates_removed": 0,
        "containment_removed": 0,
        "gpt_quality_removed": 0,
    }

    if not items:
        stats["output_count"] = 0
        return items, stats

    # Filter 1: Brightness
    items, n = filter_brightness(items)
    stats["brightness_removed"] = n

    if not items:
        stats["output_count"] = 0
        return items, stats

    # Filter 2: Duplicate label merge
    items, n = filter_duplicates(items)
    stats["duplicates_removed"] = n

    if not items:
        stats["output_count"] = 0
        return items, stats

    # Filter 3: Containment resolution
    items, n = filter_containment(items)
    stats["containment_removed"] = n

    if not items:
        stats["output_count"] = 0
        return items, stats

    # Filter 4: GPT quality check (optional)
    if enable_gpt_quality_check:
        items, n = filter_gpt_quality(items)
        stats["gpt_quality_removed"] = n

    stats["output_count"] = len(items)
    return items, stats
