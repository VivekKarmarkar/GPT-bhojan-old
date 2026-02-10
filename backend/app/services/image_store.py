from pathlib import Path
from uuid import uuid4

MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "media"


def save_visualization(image_bytes: bytes) -> str:
    out_dir = MEDIA_DIR / "visualizations"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}.jpg"
    (out_dir / filename).write_bytes(image_bytes)
    return f"/media/visualizations/{filename}"


def save_crop(image_bytes: bytes, label: str) -> str:
    out_dir = MEDIA_DIR / "crops"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_label = label.strip().replace(" ", "_").lower()
    filename = f"{safe_label}_{uuid4()}.jpg"
    (out_dir / filename).write_bytes(image_bytes)
    return f"/media/crops/{filename}"
