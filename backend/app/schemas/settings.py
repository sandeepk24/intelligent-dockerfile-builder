"""Application settings schemas."""

from pydantic import BaseModel, Field, HttpUrl


class SettingsResponse(BaseModel):
    ollama_base_url: str
    ollama_default_model: str
    ollama_timeout: int
    workspace_root: str
    docker_build_timeout: int
    docker_build_cpu_limit: int
    docker_build_memory_limit: str
    max_repair_attempts: int
    max_upload_size_mb: int
    max_file_count: int


class SettingsUpdateRequest(BaseModel):
    ollama_base_url: HttpUrl | None = None
    ollama_default_model: str | None = Field(default=None, min_length=1)
    ollama_timeout: int | None = Field(default=None, ge=10, le=600)
    max_repair_attempts: int | None = Field(default=None, ge=1, le=5)
