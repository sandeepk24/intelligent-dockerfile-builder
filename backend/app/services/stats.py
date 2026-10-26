"""Session-level evaluation metrics from the in-memory store."""

from __future__ import annotations

from app.db.memory_store import store
from app.schemas.health import SessionStatsResponse


def session_stats() -> SessionStatsResponse:
    validations = store.list_all_validations()
    durations = [item.build_duration_ms for item in validations if item.build_duration_ms]
    successful = [item for item in validations if item.status == "passed" and item.approved_build]
    return SessionStatsResponse(
        dockerfiles_generated=len(store.list_dockerfiles()),
        validations_run=len(validations),
        successful_builds=len(successful),
        failed_validations=sum(1 for item in validations if item.status == "failed"),
        repairs_applied=len(store.repairs),
        avg_build_time_ms=int(sum(durations) / len(durations)) if durations else None,
    )
