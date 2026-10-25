"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_WORKSPACE = str(_REPO_ROOT / "sample-projects")


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Intelligent Dockerfile Builder"
    app_version: str = "0.1.0"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "codellama:7b"
    ollama_timeout: int = 120

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Docker
    docker_build_timeout: int = 300
    docker_build_cpu_limit: int = 2
    docker_build_memory_limit: str = "2g"

    # Workspace
    workspace_root: str = _DEFAULT_WORKSPACE

    # Upload
    max_upload_size_mb: int = 50
    max_file_count: int = 500

    # Repair
    max_repair_attempts: int = 3

    # Database
    database_url: str = "sqlite+aiosqlite:///./intelligent_dockerfile_builder.db"


settings = Settings()
