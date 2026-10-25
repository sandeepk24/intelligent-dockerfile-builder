"""Project analysis endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from starlette.datastructures import UploadFile

from app.analyzers.zip_import import ZipSecurityError
from app.core.config import settings
from app.core.paths import WorkspacePathError, workspace_root
from app.schemas.project import (
    AnalyzeDirectoryRequest,
    AnalyzeDockerfileRequest,
    ProjectAnalysisResponse,
    WorkspaceListResponse,
)
from app.services import analysis as analysis_service

router = APIRouter()


@router.get("/workspace/projects", response_model=WorkspaceListResponse)
async def list_workspace_projects() -> WorkspaceListResponse:
    """List directories available under the configured workspace root."""
    return WorkspaceListResponse(
        workspace_root=str(workspace_root()),
        projects=analysis_service.list_workspace_projects(),
    )


@router.post("/projects/analyze", response_model=ProjectAnalysisResponse)
async def analyze_project(request: Request) -> ProjectAnalysisResponse:
    """Analyze a workspace directory (JSON) or an uploaded ZIP (multipart)."""
    content_type = request.headers.get("content-type", "")
    try:
        if content_type.startswith("multipart/form-data"):
            project = await _analyze_upload(request)
        else:
            body = await request.json()
            source_type = body.get("source_type", "directory")
            if source_type == "dockerfile":
                payload = AnalyzeDockerfileRequest.model_validate(body)
                project = analysis_service.analyze_dockerfile_text(payload.dockerfile, payload.name)
            else:
                payload = AnalyzeDirectoryRequest.model_validate(body)
                project = analysis_service.analyze_directory(payload.path)
    except WorkspacePathError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ZipSecurityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return analysis_service.to_analysis_response(project)


@router.get("/projects/{project_id}", response_model=ProjectAnalysisResponse)
async def get_project(project_id: str) -> ProjectAnalysisResponse:
    project = analysis_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return analysis_service.to_analysis_response(project)


async def _analyze_upload(request: Request):
    form = await request.form()
    upload = form.get("file")
    if not isinstance(upload, UploadFile) or not hasattr(upload, "read"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A ZIP file field named 'file' is required",
        )
    content = await upload.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="ZIP exceeds the configured upload size limit",
        )
    filename = upload.filename or "project.zip"
    lowered = filename.lower()
    if lowered.endswith(".zip"):
        return analysis_service.analyze_zip_bytes(content, filename)
    if lowered in {"dockerfile", "dockerfile.txt"} or lowered.endswith(".dockerfile"):
        text = content.decode("utf-8", errors="replace")
        return analysis_service.analyze_dockerfile_text(text, Path(filename).stem)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Upload a .zip archive or a Dockerfile",
    )
