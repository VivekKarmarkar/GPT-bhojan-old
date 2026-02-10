"""Food segmentation via lang-segment-anything on Replicate.

Uses text-prompted SAM segmentation — each food item name is sent as a
text prompt and the model returns a pixel-level binary mask.  No bounding
boxes are shown to the user; only colored mask overlays with labels.
"""

import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import numpy as np
import replicate
from PIL import Image, ImageDraw, ImageFont

from app.utils.image import bytes_to_numpy_rgb, download_image, numpy_rgb_to_jpeg_bytes

LANG_SAM_MODEL = (
    "tmappdev/lang-segment-anything:"
    "891411c38a6ed2d44c004b7b9e44217df7a5b07848f29ddefd2e28bc7cbf93bc"
)

COLORS = [
    (255, 99, 71),   # tomato
    (50, 205, 50),   # lime green
    (65, 105, 225),  # royal blue
    (255, 215, 0),   # gold
    (148, 103, 189), # purple
    (255, 127, 80),  # coral
]


@dataclass
class SegmentedItem:
    label: str
    mask: np.ndarray = field(default_factory=lambda: np.zeros((1, 1), dtype=bool), repr=False)
    crop_bytes: bytes = field(default=b"", repr=False)
    confidence: float = 1.0


def segment_single_item(image_bytes: bytes, item_name: str) -> SegmentedItem | None:
    """Call lang-segment-anything for ONE food item, return mask + crop."""
    try:
        output = replicate.run(
            LANG_SAM_MODEL,
            input={
                "image": io.BytesIO(image_bytes),
                "text_prompt": item_name,
            },
        )
        mask_url = str(output)
        mask_bytes = download_image(mask_url)
        mask_img = Image.open(io.BytesIO(mask_bytes)).convert("L")
        mask_arr = np.array(mask_img) > 128  # threshold to boolean

        if not mask_arr.any():
            return None

        crop = extract_crop_from_mask(image_bytes, mask_arr)
        return SegmentedItem(
            label=item_name,
            mask=mask_arr,
            crop_bytes=crop,
        )
    except Exception:
        return None


def segment_all_items(
    image_bytes: bytes, item_names: list[str],
) -> list[SegmentedItem]:
    """Run N parallel lang-segment-anything calls, one per food item."""
    items: list[SegmentedItem] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(segment_single_item, image_bytes, name): name
            for name in item_names
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                items.append(result)
    return items


def build_visualization(image_bytes: bytes, items: list[SegmentedItem]) -> bytes:
    """Alpha-blend colored mask overlays onto original image with labels."""
    img = bytes_to_numpy_rgb(image_bytes).copy()
    h, w = img.shape[:2]

    for i, item in enumerate(items):
        mask = item.mask
        if mask.shape != (h, w):
            # Resize mask to match image if needed
            mask_img = Image.fromarray(mask.astype(np.uint8) * 255)
            mask_img = mask_img.resize((w, h), Image.NEAREST)
            mask = np.array(mask_img) > 128

        color = np.array(COLORS[i % len(COLORS)], dtype=np.float32)
        # Alpha-blend: 50% mask color + 50% original pixels
        img[mask] = (0.5 * color + 0.5 * img[mask].astype(np.float32)).astype(np.uint8)

    # Draw labels at mask centroids
    result = Image.fromarray(img)
    draw = ImageDraw.Draw(result)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
        )
    except (OSError, IOError):
        font = ImageFont.load_default()

    for i, item in enumerate(items):
        mask = item.mask
        if mask.shape != (h, w):
            mask_img = Image.fromarray(mask.astype(np.uint8) * 255)
            mask_img = mask_img.resize((w, h), Image.NEAREST)
            mask = np.array(mask_img) > 128

        ys, xs = np.where(mask)
        if len(xs) == 0:
            continue
        cx = int(xs.mean())
        cy = int(ys.mean())

        label = item.label.capitalize()
        color = COLORS[i % len(COLORS)]
        bbox_text = draw.textbbox((0, 0), label, font=font)
        tw = bbox_text[2] - bbox_text[0]
        th = bbox_text[3] - bbox_text[1]
        tx = max(4, cx - tw // 2)
        ty = max(4, cy - th // 2)

        pad = 4
        draw.rounded_rectangle(
            [tx - pad, ty - pad, tx + tw + pad, ty + th + pad],
            radius=6,
            fill=(0, 0, 0, 180),
        )
        draw.text((tx, ty), label, fill=(255, 255, 255), font=font)

    return numpy_rgb_to_jpeg_bytes(np.array(result))


def extract_crop_from_mask(image_bytes: bytes, mask: np.ndarray) -> bytes:
    """Crop the food item using its mask — food pixels on black background."""
    img = bytes_to_numpy_rgb(image_bytes)
    h, w = img.shape[:2]

    if mask.shape != (h, w):
        mask_img = Image.fromarray(mask.astype(np.uint8) * 255)
        mask_img = mask_img.resize((w, h), Image.NEAREST)
        mask = np.array(mask_img) > 128

    ys, xs = np.where(mask)
    if len(xs) == 0:
        return numpy_rgb_to_jpeg_bytes(np.zeros((64, 64, 3), dtype=np.uint8))

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1

    cropped = img[y0:y1, x0:x1].copy()
    crop_mask = mask[y0:y1, x0:x1]
    # Black out non-food pixels
    cropped[~crop_mask] = 0

    return numpy_rgb_to_jpeg_bytes(cropped)


def segment_crop(
    original_image_bytes: bytes,
    crop_bytes: bytes,
    item_name: str,
    bbox: tuple[int, int, int, int],  # (x1, y1, x2, y2)
    full_image_shape: tuple[int, int],  # (height, width)
) -> SegmentedItem | None:
    """Segment a cropped food item via lang-SAM, then map mask back to full image coordinates."""
    try:
        # Call lang-SAM on the CROP (not full image)
        output = replicate.run(
            LANG_SAM_MODEL,
            input={
                "image": io.BytesIO(crop_bytes),
                "text_prompt": item_name,
            },
        )
        mask_url = str(output)
        mask_bytes = download_image(mask_url)
        mask_img = Image.open(io.BytesIO(mask_bytes)).convert("L")
        crop_mask = np.array(mask_img) > 128  # threshold to boolean

        if not crop_mask.any():
            return None

        x1, y1, x2, y2 = bbox
        crop_h, crop_w = y2 - y1, x2 - x1

        # Resize mask to match crop dimensions if needed
        if crop_mask.shape != (crop_h, crop_w):
            resized = Image.fromarray(crop_mask.astype(np.uint8) * 255)
            resized = resized.resize((crop_w, crop_h), Image.NEAREST)
            crop_mask = np.array(resized) > 128

        # Create full-size mask and place crop mask at correct offset
        img_h, img_w = full_image_shape
        full_mask = np.zeros((img_h, img_w), dtype=bool)
        full_mask[y1:y2, x1:x2] = crop_mask

        if not full_mask.any():
            return None

        # Extract food-on-black crop using the full mask
        food_crop = extract_crop_from_mask(original_image_bytes, full_mask)

        return SegmentedItem(
            label=item_name,
            mask=full_mask,
            crop_bytes=food_crop,
            confidence=1.0,
        )
    except Exception:
        return None


def segment_all_crops(
    original_image_bytes: bytes,
    crops: list[dict],  # each: {"crop_bytes": bytes, "label": str, "bbox": tuple, "confidence": float}
    full_image_shape: tuple[int, int],  # (height, width)
) -> list[SegmentedItem]:
    """Run parallel crop-to-SAM segmentation for all confirmed food items."""
    items: list[SegmentedItem] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(
                segment_crop,
                original_image_bytes,
                crop["crop_bytes"],
                crop["label"],
                crop["bbox"],
                full_image_shape,
            ): crop["label"]
            for crop in crops
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                items.append(result)
    return items
