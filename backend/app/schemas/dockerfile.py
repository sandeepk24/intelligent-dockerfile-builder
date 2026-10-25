"""Request and response schemas for Dockerfile generation."""

from datetime import datetime

from pydantic import BaseModel, Field


class GenerateDockerfileRequest(BaseModel):
    project_id: str
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
    created_at: datetime


class DockerfileHistoryResponse(BaseModel):
    items: list[DockerfileSummary]
