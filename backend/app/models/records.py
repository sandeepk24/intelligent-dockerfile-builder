"""In-memory domain records used until SQLite lands in Milestone 4."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class ProjectRecord:
    """Analyzed application metadata and sanitized source context."""

    id: str
    source_type: str
    name: str
    root_path: str
    language: str | None = None
    framework: str | None = None
    entry_point: str | None = None
    runtime_version: str | None = None
    dependencies: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    build_command: str | None = None
    start_command: str | None = None
    has_dockerfile: bool = False
    existing_dockerfile: str | None = None
    file_tree: list[str] = field(default_factory=list)
    key_files: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class DockerfileRecord:
    """Generated Dockerfile artifacts and AI explanations."""

    id: str
    project_id: str
    dockerfile: str
    dockerignore: str
    explanation: str
    decisions: list[str]
    model: str
    instructions: str | None = None
    status: str = "generated"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class JobRecord:
    """Background generation or validation job."""

    id: str
    job_type: str
    status: str = "pending"
    dockerfile_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
