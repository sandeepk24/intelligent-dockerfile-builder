"""Dockerfile generation, retrieval, and history endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.config import settings
from app.schemas.dockerfile import (
    DockerfileHistoryResponse,
    DockerfileResponse,
    GenerateDockerfileRequest,
    JobResponse,
    OptimizeDockerfileRequest,
    UpdateDockerfileRequest,
)
from app.schemas.validation import (
    RepairDockerfileRequest,
    RepairListResponse,
    ValidateDockerfileRequest,
    ValidationListResponse,
)
from app.services import generation as generation_service
from app.services import repair as repair_service
from app.services import validation as validation_service
from app.services.repair import RepairRequestError
from app.services.validation import ValidationRequestError

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


@router.post(
    "/dockerfiles/optimize", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED
)
async def optimize_dockerfile(
    body: OptimizeDockerfileRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    try:
        job = generation_service.create_optimize_job(body.project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    model = body.model or settings.ollama_default_model
    background_tasks.add_task(
        generation_service.run_optimize_job,
        job.id,
        body.project_id,
        model,
        body.dockerfile,
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


@router.post(
    "/dockerfiles/{dockerfile_id}/validate",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def validate_dockerfile(
    dockerfile_id: str,
    body: ValidateDockerfileRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    try:
        job = validation_service.create_validation_job(
            dockerfile_id,
            approve_build=body.approve_build,
            confirm_untrusted_execution=body.confirm_untrusted_execution,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    background_tasks.add_task(
        validation_service.run_validation_job,
        job.id,
        dockerfile_id,
        approve_build=body.approve_build,
        run_trivy=body.run_trivy,
        run_startup_check=body.run_startup_check,
    )
    return generation_service.to_job_response(job)


@router.get("/dockerfiles/{dockerfile_id}/validations", response_model=ValidationListResponse)
async def list_validations(dockerfile_id: str) -> ValidationListResponse:
    if generation_service.get_dockerfile(dockerfile_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dockerfile not found")
    items = [
        validation_service.to_validation_response(item)
        for item in validation_service.list_validations(dockerfile_id)
    ]
    return ValidationListResponse(items=items)


@router.post(
    "/dockerfiles/{dockerfile_id}/repair",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def repair_dockerfile(
    dockerfile_id: str,
    body: RepairDockerfileRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    try:
        job, attempt = repair_service.create_repair_job(dockerfile_id, body.validation_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RepairRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    model = body.model or settings.ollama_default_model
    background_tasks.add_task(
        repair_service.run_repair_job,
        job.id,
        dockerfile_id,
        body.validation_id,
        attempt,
        model,
        body.instructions,
    )
    return generation_service.to_job_response(job)


@router.get("/dockerfiles/{dockerfile_id}/repairs", response_model=RepairListResponse)
async def list_repairs(dockerfile_id: str) -> RepairListResponse:
    if generation_service.get_dockerfile(dockerfile_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dockerfile not found")
    items = [
        repair_service.to_repair_response(item)
        for item in repair_service.list_repairs(dockerfile_id)
    ]
    return RepairListResponse(
        items=items,
        attempts_used=repair_service.count_lineage_repairs(dockerfile_id),
        max_attempts=settings.max_repair_attempts,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    job = generation_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return generation_service.to_job_response(job)
