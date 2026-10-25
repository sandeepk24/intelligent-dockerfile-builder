"""Health and model discovery schemas."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    ollama_connected: bool
    ollama_url: str


class OllamaModel(BaseModel):
    """Single Ollama model info."""

    name: str
    size: int
    modified_at: datetime | None = None


class ModelsResponse(BaseModel):
    """Available models response."""

    models: list[OllamaModel]
    default_model: str
