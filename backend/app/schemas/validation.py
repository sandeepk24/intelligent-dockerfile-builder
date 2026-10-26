"""Validation and repair request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ValidateDockerfileRequest(BaseModel):
    """Start a validation job.

    Docker builds execute untrusted project code. `approve_build` and
    `confirm_untrusted_execution` must both be true before a build runs.
    """

    approve_build: bool = False
    confirm_untrusted_execution: bool = False
    run_trivy: bool = False
    run_startup_check: bool = False


class RepairDockerfileRequest(BaseModel):
    validation_id: str
    model: str | None = None
    instructions: str | None = Field(default=None, max_length=4000)


class ToolStepResult(BaseModel):
    status: str
    reason: str | None = None
    findings: list[dict] = Field(default_factory=list)
    log: str | None = None
    image_tag: str | None = None
    duration_ms: int | None = None
    image_size_bytes: int | None = None
    finding_count: int | None = None
    returncode: int | None = None
    stderr: str | None = None


class ValidationResponse(BaseModel):
    id: str
    dockerfile_id: str
    status: str
    approved_build: bool
    lint: dict
    build: dict
    image_size_bytes: int | None = None
    build_duration_ms: int | None = None
    trivy: dict | None = None
    startup: dict | None = None
    error_log: str | None = None
    created_at: datetime


class ValidationListResponse(BaseModel):
    items: list[ValidationResponse]


class RepairResponse(BaseModel):
    id: str
    validation_id: str
    source_dockerfile_id: str
    result_dockerfile_id: str | None = None
    attempt: int
    root_cause: str
    explanation: str
    decisions: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime


class RepairListResponse(BaseModel):
    items: list[RepairResponse]
    attempts_used: int
    max_attempts: int
