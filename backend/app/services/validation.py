"""Background Dockerfile validation jobs."""

from __future__ import annotations

from uuid import uuid4

from app.analyzers.dockerfile_review import issues_to_dicts, review_dockerfile
from app.core.config import settings
from app.core.logging import get_logger
from app.db.memory_store import store
from app.models.records import JobRecord, ValidationRecord
from app.schemas.validation import ValidationResponse
from app.validators.docker_build import build_image, docker_available, remove_image
from app.validators.hadolint import run_hadolint
from app.validators.sandbox import cleanup_context, prepare_build_context
from app.validators.startup import check_startup
from app.validators.trivy import scan_image, trivy_available

logger = get_logger(__name__)


class ValidationRequestError(ValueError):
    """Raised when a validation request is not allowed to proceed."""


def create_validation_job(
    dockerfile_id: str,
    *,
    approve_build: bool,
    confirm_untrusted_execution: bool,
) -> JobRecord:
    record = store.get_dockerfile(dockerfile_id)
    if record is None:
        raise FileNotFoundError("Dockerfile not found")
    if approve_build and not confirm_untrusted_execution:
        raise ValidationRequestError(
            "Building untrusted project code requires confirm_untrusted_execution=true"
        )
    job = JobRecord(
        id=str(uuid4()),
        job_type="validate",
        status="pending",
        dockerfile_id=dockerfile_id,
    )
    return store.save_job(job)


async def run_validation_job(
    job_id: str,
    dockerfile_id: str,
    *,
    approve_build: bool,
    run_trivy: bool,
    run_startup_check: bool,
) -> None:
    store.update_job(job_id, status="running")
    context = None
    image_tag = None
    try:
        dockerfile = store.get_dockerfile(dockerfile_id)
        if dockerfile is None:
            raise FileNotFoundError("Dockerfile not found")
        project = store.get_project(dockerfile.project_id)
        if project is None:
            raise FileNotFoundError("Project not found")

        static_findings = issues_to_dicts(
            review_dockerfile(dockerfile.dockerfile, ports=project.ports)
        )
        context = prepare_build_context(project, dockerfile)
        lint = await run_hadolint(context / "Dockerfile")
        lint["static_findings"] = static_findings

        build: dict = {
            "status": "skipped",
            "reason": "Docker build was not approved",
        }
        trivy_result = None
        startup_result = None
        image_size = None
        duration = None
        error_log = None

        should_build = approve_build and settings.docker_allow_builds
        if should_build:
            image_tag = f"idf-validate-{dockerfile_id[:8]}-{uuid4().hex[:8]}"
            build = await build_image(context, image_tag)
            image_size = build.get("image_size_bytes")
            duration = build.get("duration_ms")
            if build.get("status") == "failed":
                error_log = build.get("log")
            if build.get("status") == "passed" and image_tag:
                if run_trivy:
                    trivy_result = await scan_image(image_tag)
                if run_startup_check:
                    startup_result = await check_startup(
                        image_tag, name=f"idf-run-{uuid4().hex[:10]}"
                    )
                    if startup_result.get("status") == "failed":
                        error_log = startup_result.get("log") or error_log

        status = _overall_status(lint, build, trivy_result, startup_result, approved=should_build)
        validation = ValidationRecord(
            id=str(uuid4()),
            dockerfile_id=dockerfile_id,
            status=status,
            lint=lint,
            build=build,
            image_size_bytes=image_size,
            build_duration_ms=duration,
            trivy=trivy_result,
            startup=startup_result,
            error_log=error_log,
            approved_build=should_build,
        )
        store.save_validation(validation)
        store.update_job(job_id, status="completed", validation_id=validation.id)
    except Exception as exc:
        logger.exception("Validation job %s failed", job_id)
        store.update_job(job_id, status="failed", error=str(exc))
    finally:
        if image_tag:
            await remove_image(image_tag)
        if context is not None:
            cleanup_context(context)


def get_validation(validation_id: str) -> ValidationRecord | None:
    return store.get_validation(validation_id)


def list_validations(dockerfile_id: str) -> list[ValidationRecord]:
    return store.list_validations(dockerfile_id)


def to_validation_response(record: ValidationRecord) -> ValidationResponse:
    return ValidationResponse(
        id=record.id,
        dockerfile_id=record.dockerfile_id,
        status=record.status,
        approved_build=record.approved_build,
        lint=record.lint,
        build=record.build,
        image_size_bytes=record.image_size_bytes,
        build_duration_ms=record.build_duration_ms,
        trivy=record.trivy,
        startup=record.startup,
        error_log=record.error_log,
        created_at=record.created_at,
    )


def toolchain_status() -> dict[str, bool]:
    import shutil

    return {
        "docker": docker_available(),
        "hadolint": shutil.which(settings.hadolint_bin) is not None
        or shutil.which("hadolint") is not None,
        "trivy": trivy_available(),
    }


def _overall_status(
    lint: dict,
    build: dict,
    trivy_result: dict | None,
    startup_result: dict | None,
    *,
    approved: bool,
) -> str:
    lint_failed = lint.get("status") == "failed"
    build_failed = build.get("status") == "failed"
    startup_failed = bool(startup_result and startup_result.get("status") == "failed")
    if lint_failed or build_failed or startup_failed:
        return "failed"
    if approved and build.get("status") == "passed":
        return "passed"
    return "lint_only"
