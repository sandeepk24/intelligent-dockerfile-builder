"""Collect evaluation events for dashboard metrics."""

from __future__ import annotations

from uuid import uuid4

from app.db.store import store
from app.models.records import DockerfileRecord, EvaluationRecord, ValidationRecord


def record_dockerfile_event(record: DockerfileRecord) -> EvaluationRecord:
    project = store.get_project(record.project_id)
    event = EvaluationRecord(
        id=str(uuid4()),
        event=record.status,
        status=record.status,
        dockerfile_id=record.id,
        project_id=record.project_id,
        language=project.language if project else None,
        framework=project.framework if project else None,
        model=record.model,
    )
    return store.save_evaluation(event)


def record_validation_event(
    validation: ValidationRecord, dockerfile: DockerfileRecord
) -> EvaluationRecord:
    project = store.get_project(dockerfile.project_id)
    lint = validation.lint or {}
    findings = list(lint.get("findings") or []) + list(lint.get("static_findings") or [])
    trivy = validation.trivy or {}
    trivy_count = int(trivy.get("finding_count") or len(trivy.get("findings") or []))
    event = EvaluationRecord(
        id=str(uuid4()),
        event="validated",
        status=validation.status,
        dockerfile_id=validation.dockerfile_id,
        validation_id=validation.id,
        project_id=dockerfile.project_id,
        language=project.language if project else None,
        framework=project.framework if project else None,
        model=dockerfile.model,
        image_size_bytes=validation.image_size_bytes,
        build_duration_ms=validation.build_duration_ms,
        lint_finding_count=len(findings),
        trivy_finding_count=trivy_count,
    )
    return store.save_evaluation(event)
