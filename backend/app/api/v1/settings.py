"""Application settings endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.llm.ollama_client import ollama_client
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest

router = APIRouter()


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return SettingsResponse(
        ollama_base_url=settings.ollama_base_url,
        ollama_default_model=settings.ollama_default_model,
        ollama_timeout=settings.ollama_timeout,
        workspace_root=settings.workspace_root,
        docker_build_timeout=settings.docker_build_timeout,
        docker_build_cpu_limit=settings.docker_build_cpu_limit,
        docker_build_memory_limit=settings.docker_build_memory_limit,
        max_repair_attempts=settings.max_repair_attempts,
        max_upload_size_mb=settings.max_upload_size_mb,
        max_file_count=settings.max_file_count,
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdateRequest) -> SettingsResponse:
    if body.ollama_base_url is not None:
        settings.ollama_base_url = str(body.ollama_base_url).rstrip("/")
        ollama_client.base_url = settings.ollama_base_url
    if body.ollama_default_model is not None:
        settings.ollama_default_model = body.ollama_default_model
    if body.ollama_timeout is not None:
        settings.ollama_timeout = body.ollama_timeout
        ollama_client.timeout = body.ollama_timeout
    if body.max_repair_attempts is not None:
        settings.max_repair_attempts = body.max_repair_attempts
    return await get_settings()
