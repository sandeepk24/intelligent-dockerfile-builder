"""Health and model discovery schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    ollama_connected: bool
    ollama_url: str
    docker_available: bool = False
    hadolint_available: bool = False
    trivy_available: bool = False
    persistence: str = "memory"


class OllamaModel(BaseModel):
    """Single Ollama model info."""

    name: str
    size: int
    modified_at: datetime | None = None


class ModelsResponse(BaseModel):
    """Available models response."""

    models: list[OllamaModel]
    default_model: str


class CountBucket(BaseModel):
    key: str
    count: int


class SessionStatsResponse(BaseModel):
    """Dashboard metrics from persisted (or in-memory) evaluation data."""

    dockerfiles_generated: int
    validations_run: int
    successful_builds: int
    failed_validations: int
    repairs_applied: int
    avg_build_time_ms: int | None = None
    avg_image_size_bytes: int | None = None
    build_success_rate: float | None = None
    persistence: str = "memory"
    by_language: list[CountBucket] = Field(default_factory=list)
    by_model: list[CountBucket] = Field(default_factory=list)
    by_status: list[CountBucket] = Field(default_factory=list)
