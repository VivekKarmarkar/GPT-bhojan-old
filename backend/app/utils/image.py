import base64
import io

import httpx
import numpy as np
from PIL import Image


def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def resize_if_needed(image_bytes: bytes, max_dim: int = 2048) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    if max(img.size) <= max_dim:
        return image_bytes
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    img.save(buf, format=fmt)
    return buf.getvalue()


def image_bytes_to_data_uri(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    b64 = image_bytes_to_base64(image_bytes)
    return f"data:{mime};base64,{b64}"


def download_image(url: str) -> bytes:
    resp = httpx.get(url, follow_redirects=True, timeout=30.0)
    resp.raise_for_status()
    return resp.content


def bytes_to_numpy_rgb(image_bytes: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))


def numpy_rgb_to_jpeg_bytes(arr: np.ndarray, quality: int = 85) -> bytes:
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
