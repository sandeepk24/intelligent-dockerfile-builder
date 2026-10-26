"""Health and model discovery schemas."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    ollama_connected: bool
    ollama_url: str
    docker_available: bool = False
    hadolint_available: bool = False
    trivy_available: bool = False


class OllamaModel(BaseModel):
    """Single Ollama model info."""

    name: str
    size: int
    modified_at: datetime | None = None


class ModelsResponse(BaseModel):
    """Available models response."""

    models: list[OllamaModel]
    default_model: str


class SessionStatsResponse(BaseModel):
    """In-memory session metrics until SQLite lands in Milestone 4."""

    dockerfiles_generated: int
    validations_run: int
    successful_builds: int
    failed_validations: int
    repairs_applied: int
    avg_build_time_ms: int | None = None
