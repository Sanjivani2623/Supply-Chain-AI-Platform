"""
FastAPI application entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import Base, engine
from app.api.v1.router import api_router
import app.models  # noqa: F401 ensures all models are registered on Base.metadata

configure_logging(settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(
    title="AI-Driven Supply Chain Disruption Predictor & Inventory Optimization API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    # In production, use Alembic migrations instead of create_all.
    Base.metadata.create_all(bind=engine)
    logger.info("app.startup", environment=settings.ENVIRONMENT, database=settings.DATABASE_URL)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
