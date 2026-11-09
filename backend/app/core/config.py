"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
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
    ollama_timeout: int = Field(default=120, ge=10, le=600)
    ollama_health_timeout: int = Field(default=5, ge=1, le=60)
    ollama_list_timeout: int = Field(default=10, ge=1, le=120)

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Docker
    docker_build_timeout: int = Field(default=300, ge=30, le=3600)
    docker_run_timeout: int = Field(default=30, ge=5, le=300)
    docker_inspect_timeout: int = Field(default=15, ge=1, le=120)
    docker_logs_timeout: int = Field(default=10, ge=1, le=120)
    docker_remove_timeout: int = Field(default=30, ge=1, le=300)
    docker_build_cpu_limit: int = 2
    docker_build_memory_limit: str = "2g"
    docker_sandbox_dir: str = "/tmp/intelligent-dockerfile-sandbox"
    docker_allow_builds: bool = True
    startup_check_seconds: int = 8

    # External tools
    hadolint_bin: str = "hadolint"
    hadolint_timeout: int = Field(default=30, ge=5, le=300)
    trivy_bin: str = "trivy"
    trivy_timeout: int = Field(default=180, ge=30, le=1800)
    trivy_enabled: bool = False

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
