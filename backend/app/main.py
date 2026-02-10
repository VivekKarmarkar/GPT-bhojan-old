from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings  # noqa: F401 — validates env on startup
from app.routers import health, analyze, meals, food_items


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: config is already validated by importing settings
    yield
    # Shutdown: nothing to clean up yet


app = FastAPI(
    title="GPT-Bhojan API",
    description="Strava for Food — AI-powered food analysis backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(meals.router)
app.include_router(food_items.router)

# Serve saved visualizations and crops
media_dir = Path(__file__).resolve().parent.parent / "media"
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
