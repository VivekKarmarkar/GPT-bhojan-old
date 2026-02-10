from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services.gpt_service import check_api_key
from app.services.detection import check_replicate_token

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        openai=check_api_key(),
        replicate=check_replicate_token(),
    )
