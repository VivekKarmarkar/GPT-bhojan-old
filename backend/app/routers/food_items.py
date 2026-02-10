from fastapi import APIRouter

from app.models.schemas import FoodItemRecord

router = APIRouter(prefix="/api", tags=["food-items"])


@router.get("/food-items", response_model=list[FoodItemRecord])
async def list_food_items():
    return []


@router.get("/food-items/{item_id}", response_model=FoodItemRecord)
async def get_food_item(item_id: str):
    return FoodItemRecord(id=item_id)


@router.patch("/food-items/{item_id}/like")
async def toggle_like(item_id: str):
    return {"id": item_id, "liked": True}
