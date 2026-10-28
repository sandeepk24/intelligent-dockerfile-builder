"""Domain records shared by the memory store and SQLite persistence."""

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
    original_dockerfile: str | None = None
    issues: list[dict] = field(default_factory=list)
    parent_id: str | None = None
    repair_attempt: int = 0
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class JobRecord:
    """Background generation or validation job."""

    id: str
    job_type: str
    status: str = "pending"
    dockerfile_id: str | None = None
    validation_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class ValidationRecord:
    """One validation run: lint, optional build, scan, and startup check."""

    id: str
    dockerfile_id: str
    status: str
    lint: dict = field(default_factory=dict)
    build: dict = field(default_factory=dict)
    image_size_bytes: int | None = None
    build_duration_ms: int | None = None
    trivy: dict | None = None
    startup: dict | None = None
    error_log: str | None = None
    approved_build: bool = False
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class RepairRecord:
    """One AI repair attempt against a failed validation."""

    id: str
    validation_id: str
    source_dockerfile_id: str
    result_dockerfile_id: str | None = None
    attempt: int = 1
    root_cause: str = ""
    explanation: str = ""
    decisions: list[str] = field(default_factory=list)
    status: str = "proposed"
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class EvaluationRecord:
    """One evaluation event used for dashboard metrics."""

    id: str
    event: str
    status: str
    dockerfile_id: str | None = None
    validation_id: str | None = None
    project_id: str | None = None
    language: str | None = None
    framework: str | None = None
    model: str | None = None
    image_size_bytes: int | None = None
    build_duration_ms: int | None = None
    lint_finding_count: int = 0
    trivy_finding_count: int = 0
    created_at: datetime = field(default_factory=utcnow)
