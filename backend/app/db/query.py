"""Shared filtering for Dockerfile history."""

from __future__ import annotations

from app.models.records import DockerfileRecord, ProjectRecord


def matches_history_filters(
    record: DockerfileRecord,
    project: ProjectRecord | None,
    *,
    status: str | None = None,
    language: str | None = None,
    model: str | None = None,
    query: str | None = None,
) -> bool:
    if status and record.status != status:
        return False
    if model and record.model != model:
        return False
    if language and (project is None or project.language != language):
        return False
    if query:
        haystack = " ".join(
            part
            for part in (
                record.project_id,
                record.model,
                record.status,
                project.name if project else "",
                project.language if project else "",
                project.framework if project else "",
            )
            if part
        ).lower()
        if query.lower() not in haystack:
            return False
    return True
