"""Health and model discovery endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.llm.ollama_client import ollama_client
from app.schemas.health import (
    HealthResponse,
    ModelsResponse,
    OllamaModel,
    SessionStatsResponse,
)
from app.services.stats import session_stats
from app.services.validation import toolchain_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check backend health and Ollama connectivity."""
    connected = await ollama_client.is_connected()
    tools = toolchain_status()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        ollama_connected=connected,
        ollama_url=settings.ollama_base_url,
        docker_available=tools["docker"],
        hadolint_available=tools["hadolint"],
        trivy_available=tools["trivy"],
    )


@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats() -> SessionStatsResponse:
    """Return in-memory dashboard metrics for this process."""
    return session_stats()


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """List available Ollama models."""
    raw_models = await ollama_client.list_models()
    models = []
    for m in raw_models:
        modified = None
        if m.get("modified_at"):
            try:
                modified = datetime.fromisoformat(m["modified_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                modified = None
        models.append(
            OllamaModel(
                name=m.get("name", "unknown"),
                size=m.get("size", 0),
                modified_at=modified,
            )
        )
    return ModelsResponse(
        models=models,
        default_model=settings.ollama_default_model,
    )
