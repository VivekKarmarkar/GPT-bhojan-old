import asyncio

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import AnalyzeResponse
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_food(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    result = await asyncio.to_thread(run_pipeline, image_bytes)
    return result
