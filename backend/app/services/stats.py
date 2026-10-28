"""Dashboard evaluation metrics from the configured store."""

from __future__ import annotations

from collections import Counter

from app.db.store import store
from app.schemas.health import CountBucket, SessionStatsResponse


def session_stats() -> SessionStatsResponse:
    dockerfiles = store.list_dockerfiles()
    validations = store.list_all_validations()
    repairs = store.list_all_repairs()
    durations = [item.build_duration_ms for item in validations if item.build_duration_ms]
    sizes = [item.image_size_bytes for item in validations if item.image_size_bytes]
    approved = [item for item in validations if item.approved_build]
    successful = [item for item in approved if item.status == "passed"]
    languages: list[str] = []
    for record in dockerfiles:
        project = store.get_project(record.project_id)
        languages.append(project.language if project and project.language else "unknown")
    return SessionStatsResponse(
        dockerfiles_generated=len(dockerfiles),
        validations_run=len(validations),
        successful_builds=len(successful),
        failed_validations=sum(1 for item in validations if item.status == "failed"),
        repairs_applied=len(repairs),
        avg_build_time_ms=int(sum(durations) / len(durations)) if durations else None,
        avg_image_size_bytes=int(sum(sizes) / len(sizes)) if sizes else None,
        build_success_rate=(len(successful) / len(approved)) if approved else None,
        persistence=store.kind,
        by_language=_buckets(languages),
        by_model=_buckets(item.model for item in dockerfiles),
        by_status=_buckets(item.status for item in dockerfiles),
    )


def _buckets(values) -> list[CountBucket]:
    counts = Counter(value or "unknown" for value in values)
    return [CountBucket(key=key, count=count) for key, count in counts.most_common()]
