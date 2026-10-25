"""Background Dockerfile generation jobs."""

from __future__ import annotations

from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.db.memory_store import store
from app.generators.dockerfile import generate_from_project, project_to_analysis
from app.generators.dockerignore import generate_dockerignore
from app.llm.factory import get_llm_provider
from app.models.records import DockerfileRecord, JobRecord, utcnow
from app.schemas.dockerfile import DockerfileResponse, DockerfileSummary, JobResponse

logger = get_logger(__name__)


def create_generation_job(project_id: str) -> JobRecord:
    project = store.get_project(project_id)
    if project is None:
        raise FileNotFoundError("Project not found")
    job = JobRecord(id=str(uuid4()), job_type="generate", status="pending")
    return store.save_job(job)


async def run_generation_job(
    job_id: str,
    project_id: str,
    model: str,
    instructions: str | None,
) -> None:
    store.update_job(job_id, status="running")
    try:
        project = store.get_project(project_id)
        if project is None:
            raise FileNotFoundError("Project not found")
        provider = get_llm_provider()
        if not await provider.is_connected():
            raise RuntimeError(
                f"Ollama is not reachable at {settings.ollama_base_url}. Start it with `ollama serve`."
            )
        generated = await generate_from_project(
            project,
            provider,
            model=model,
            instructions=instructions,
        )
        dockerignore = generate_dockerignore(project_to_analysis(project))
        record = DockerfileRecord(
            id=str(uuid4()),
            project_id=project.id,
            dockerfile=generated.dockerfile,
            dockerignore=dockerignore,
            explanation=generated.explanation,
            decisions=generated.decisions,
            model=model,
            instructions=instructions,
            status="generated",
        )
        store.save_dockerfile(record)
        store.update_job(job_id, status="completed", dockerfile_id=record.id)
    except Exception as exc:
        logger.exception("Dockerfile generation job %s failed", job_id)
        store.update_job(job_id, status="failed", error=str(exc))


def get_job(job_id: str) -> JobRecord | None:
    return store.get_job(job_id)


def get_dockerfile(dockerfile_id: str) -> DockerfileRecord | None:
    return store.get_dockerfile(dockerfile_id)


def update_dockerfile(
    dockerfile_id: str, dockerfile: str | None, dockerignore: str | None
) -> DockerfileRecord:
    record = store.get_dockerfile(dockerfile_id)
    if record is None:
        raise FileNotFoundError("Dockerfile not found")
    if dockerfile is not None:
        record.dockerfile = dockerfile
    if dockerignore is not None:
        record.dockerignore = dockerignore
    record.status = "edited"
    record.updated_at = utcnow()
    return store.save_dockerfile(record)


def list_history() -> list[DockerfileRecord]:
    return store.list_dockerfiles()


def to_job_response(job: JobRecord) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=job.status,
        job_type=job.job_type,
        dockerfile_id=job.dockerfile_id,
        error=job.error,
    )


def to_dockerfile_response(record: DockerfileRecord) -> DockerfileResponse:
    project = store.get_project(record.project_id)
    return DockerfileResponse(
        id=record.id,
        project_id=record.project_id,
        project_name=project.name if project else None,
        language=project.language if project else None,
        framework=project.framework if project else None,
        dockerfile=record.dockerfile,
        dockerignore=record.dockerignore,
        explanation=record.explanation,
        decisions=record.decisions,
        model=record.model,
        instructions=record.instructions,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def to_summary(record: DockerfileRecord) -> DockerfileSummary:
    project = store.get_project(record.project_id)
    return DockerfileSummary(
        id=record.id,
        project_id=record.project_id,
        project_name=project.name if project else None,
        language=project.language if project else None,
        framework=project.framework if project else None,
        model=record.model,
        status=record.status,
        created_at=record.created_at,
    )
