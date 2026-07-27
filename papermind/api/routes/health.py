"""Health check router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from papermind.core.config.settings import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    llm_provider: str


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """Returns the current health status of the PaperMind API."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app.version,
        env=settings.app.env,
        llm_provider=settings.llm.provider,
    )
