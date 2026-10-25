"""Dockerfile generation, retrieval, and history endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.config import settings
from app.schemas.dockerfile import (
    DockerfileHistoryResponse,
    DockerfileResponse,
    GenerateDockerfileRequest,
    JobResponse,
    UpdateDockerfileRequest,
)
from app.services import generation as generation_service

router = APIRouter()


@router.post(
    "/dockerfiles/generate", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED
)
async def generate_dockerfile(
    body: GenerateDockerfileRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    try:
        job = generation_service.create_generation_job(body.project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    model = body.model or settings.ollama_default_model
    background_tasks.add_task(
        generation_service.run_generation_job,
        job.id,
        body.project_id,
        model,
        body.instructions,
    )
    return generation_service.to_job_response(job)


@router.get("/dockerfiles/history", response_model=DockerfileHistoryResponse)
async def dockerfile_history() -> DockerfileHistoryResponse:
    items = [generation_service.to_summary(record) for record in generation_service.list_history()]
    return DockerfileHistoryResponse(items=items)


@router.get("/dockerfiles/{dockerfile_id}", response_model=DockerfileResponse)
async def get_dockerfile(dockerfile_id: str) -> DockerfileResponse:
    record = generation_service.get_dockerfile(dockerfile_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dockerfile not found")
    return generation_service.to_dockerfile_response(record)


@router.put("/dockerfiles/{dockerfile_id}", response_model=DockerfileResponse)
async def update_dockerfile(
    dockerfile_id: str, body: UpdateDockerfileRequest
) -> DockerfileResponse:
    try:
        record = generation_service.update_dockerfile(
            dockerfile_id,
            body.dockerfile,
            body.dockerignore,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return generation_service.to_dockerfile_response(record)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    job = generation_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return generation_service.to_job_response(job)
