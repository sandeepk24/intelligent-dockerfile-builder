"""AI repair of failed Docker validations. Never runs host commands from the model."""

from __future__ import annotations

from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.db.store import store
from app.evaluators.metrics import record_dockerfile_event
from app.generators.dockerfile import project_to_analysis, repair_from_failure
from app.generators.dockerignore import generate_dockerignore
from app.llm.factory import get_llm_provider
from app.models.records import DockerfileRecord, JobRecord, RepairRecord
from app.schemas.validation import RepairResponse

logger = get_logger(__name__)


class RepairRequestError(ValueError):
    """Raised when a repair cannot be started."""


def create_repair_job(dockerfile_id: str, validation_id: str) -> tuple[JobRecord, int]:
    dockerfile = store.get_dockerfile(dockerfile_id)
    if dockerfile is None:
        raise FileNotFoundError("Dockerfile not found")
    attempts = count_lineage_repairs(dockerfile_id)
    if attempts >= settings.max_repair_attempts:
        raise RepairRequestError(
            f"Maximum repair attempts ({settings.max_repair_attempts}) already used"
        )
    validation = store.get_validation(validation_id)
    if validation is None:
        raise FileNotFoundError("Validation not found")
    if validation.dockerfile_id != dockerfile_id:
        raise RepairRequestError("Validation does not belong to this Dockerfile")
    if validation.status != "failed":
        raise RepairRequestError("Repair is only available after a failed validation")

    job = JobRecord(
        id=str(uuid4()),
        job_type="repair",
        status="pending",
        dockerfile_id=dockerfile_id,
        validation_id=validation_id,
    )
    return store.save_job(job), attempts + 1


async def run_repair_job(
    job_id: str,
    dockerfile_id: str,
    validation_id: str,
    attempt: int,
    model: str,
    instructions: str | None,
) -> None:
    store.update_job(job_id, status="running")
    try:
        dockerfile = store.get_dockerfile(dockerfile_id)
        validation = store.get_validation(validation_id)
        if dockerfile is None or validation is None:
            raise FileNotFoundError("Dockerfile or validation not found")
        project = store.get_project(dockerfile.project_id)
        if project is None:
            raise FileNotFoundError("Project not found")

        provider = get_llm_provider()
        if not await provider.is_connected():
            raise RuntimeError(
                f"Ollama is not reachable at {settings.ollama_base_url}. Start it with `ollama serve`."
            )

        lint_findings = list(validation.lint.get("findings") or [])
        lint_findings.extend(validation.lint.get("static_findings") or [])
        repaired = await repair_from_failure(
            project,
            provider,
            model=model,
            dockerfile=dockerfile.dockerfile,
            error_log=validation.error_log or validation.build.get("log") or "Build failed",
            lint_findings=lint_findings,
            instructions=instructions,
        )
        dockerignore = generate_dockerignore(project_to_analysis(project))
        result = DockerfileRecord(
            id=str(uuid4()),
            project_id=project.id,
            dockerfile=repaired.dockerfile,
            dockerignore=dockerignore,
            explanation=repaired.explanation,
            decisions=repaired.decisions,
            model=model,
            instructions=instructions,
            status="repaired",
            original_dockerfile=dockerfile.dockerfile,
            parent_id=dockerfile.id,
            repair_attempt=attempt,
        )
        store.save_dockerfile(result)
        record_dockerfile_event(result)
        repair = RepairRecord(
            id=str(uuid4()),
            validation_id=validation_id,
            source_dockerfile_id=dockerfile_id,
            result_dockerfile_id=result.id,
            attempt=attempt,
            root_cause=repaired.root_cause or "See explanation",
            explanation=repaired.explanation,
            decisions=repaired.decisions,
            status="proposed",
        )
        store.save_repair(repair)
        store.update_job(job_id, status="completed", dockerfile_id=result.id)
    except Exception as exc:
        logger.exception("Repair job %s failed", job_id)
        store.update_job(job_id, status="failed", error=str(exc))


def count_lineage_repairs(dockerfile_id: str) -> int:
    chain: set[str] = set()
    current: str | None = dockerfile_id
    while current and current not in chain:
        chain.add(current)
        record = store.get_dockerfile(current)
        current = record.parent_id if record else None
    return sum(1 for item in store.list_all_repairs() if item.source_dockerfile_id in chain)


def list_repairs(dockerfile_id: str) -> list[RepairRecord]:
    return store.list_repairs(dockerfile_id)


def to_repair_response(record: RepairRecord) -> RepairResponse:
    return RepairResponse(
        id=record.id,
        validation_id=record.validation_id,
        source_dockerfile_id=record.source_dockerfile_id,
        result_dockerfile_id=record.result_dockerfile_id,
        attempt=record.attempt,
        root_cause=record.root_cause,
        explanation=record.explanation,
        decisions=record.decisions,
        status=record.status,
        created_at=record.created_at,
    )
