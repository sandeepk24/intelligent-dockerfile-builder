"""Request and response schemas for Dockerfile generation."""

from datetime import datetime

from pydantic import BaseModel, Field


class DockerfileIssueResponse(BaseModel):
    code: str
    severity: str
    title: str
    detail: str
    suggestion: str
    line: int | None = None


class GenerateDockerfileRequest(BaseModel):
    project_id: str
    model: str | None = None
    instructions: str | None = Field(default=None, max_length=4000)


class OptimizeDockerfileRequest(BaseModel):
    project_id: str
    dockerfile: str | None = Field(default=None, max_length=200_000)
    model: str | None = None
    instructions: str | None = Field(default=None, max_length=4000)


class UpdateDockerfileRequest(BaseModel):
    dockerfile: str | None = None
    dockerignore: str | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    job_type: str | None = None
    dockerfile_id: str | None = None
    validation_id: str | None = None
    error: str | None = None


class DockerfileResponse(BaseModel):
    id: str
    project_id: str
    project_name: str | None = None
    language: str | None = None
    framework: str | None = None
    dockerfile: str
    dockerignore: str
    explanation: str
    decisions: list[str] = Field(default_factory=list)
    model: str
    instructions: str | None = None
    status: str
    original_dockerfile: str | None = None
    issues: list[DockerfileIssueResponse] = Field(default_factory=list)
    parent_id: str | None = None
    repair_attempt: int = 0
    created_at: datetime
    updated_at: datetime


class DockerfileSummary(BaseModel):
    id: str
    project_id: str
    project_name: str | None = None
    language: str | None = None
    framework: str | None = None
    model: str
    status: str
    parent_id: str | None = None
    repair_attempt: int = 0
    created_at: datetime


class DockerfileHistoryResponse(BaseModel):
    items: list[DockerfileSummary]
