from fastapi import APIRouter

from app.models.schemas import MealRecord

router = APIRouter(prefix="/api", tags=["meals"])


@router.get("/meals", response_model=list[MealRecord])
async def list_meals():
    return []


@router.get("/meals/{meal_id}", response_model=MealRecord)
async def get_meal(meal_id: str):
    return MealRecord(id=meal_id)


@router.delete("/meals/{meal_id}")
async def delete_meal(meal_id: str):
    return {"deleted": meal_id}
