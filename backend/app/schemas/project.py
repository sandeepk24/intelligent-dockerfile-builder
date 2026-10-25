"""Request and response schemas for project analysis."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeDirectoryRequest(BaseModel):
    """Analyze a project under the configured workspace root."""

    source_type: Literal["directory"] = "directory"
    path: str = Field(..., min_length=1, description="Relative path under WORKSPACE_ROOT")


class WorkspaceProject(BaseModel):
    """A directory that can be selected from the workspace root."""

    name: str
    path: str
    has_dockerfile: bool = False


class WorkspaceListResponse(BaseModel):
    workspace_root: str
    projects: list[WorkspaceProject]


class ProjectAnalysisResponse(BaseModel):
    project_id: str
    name: str
    source_type: str
    language: str | None = None
    framework: str | None = None
    entry_point: str | None = None
    runtime_version: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    ports: list[int] = Field(default_factory=list)
    build_command: str | None = None
    start_command: str | None = None
    has_dockerfile: bool = False
    file_tree: list[str] = Field(default_factory=list)
    created_at: datetime
