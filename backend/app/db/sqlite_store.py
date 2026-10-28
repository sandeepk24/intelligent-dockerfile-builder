"""SQLite-backed store with the same surface as MemoryStore."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.engine import make_engine, make_session_factory
from app.db.orm import (
    Base,
    DockerfileRow,
    EvaluationRow,
    JobRow,
    ProjectRow,
    RepairRow,
    SettingRow,
    ValidationRow,
)
from app.db.query import matches_history_filters
from app.models.records import (
    DockerfileRecord,
    EvaluationRecord,
    JobRecord,
    ProjectRecord,
    RepairRecord,
    ValidationRecord,
    utcnow,
)


class SqliteStore:
    """Persist projects, Dockerfiles, jobs, validations, repairs, and metrics."""

    def __init__(self, url: str) -> None:
        self.engine = make_engine(url)
        self._session_factory = make_session_factory(self.engine)
        Base.metadata.create_all(self.engine)

    def _session(self) -> Session:
        return self._session_factory()

    def clear(self) -> None:
        with self._session() as session:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()

    def save_project(self, project: ProjectRecord) -> ProjectRecord:
        with self._session() as session:
            row = session.get(ProjectRow, project.id) or ProjectRow(id=project.id)
            _write_project(row, project)
            session.merge(row)
            session.commit()
        return project

    def get_project(self, project_id: str) -> ProjectRecord | None:
        with self._session() as session:
            row = session.get(ProjectRow, project_id)
            return _read_project(row) if row else None

    def save_dockerfile(self, record: DockerfileRecord) -> DockerfileRecord:
        with self._session() as session:
            row = session.get(DockerfileRow, record.id) or DockerfileRow(id=record.id)
            _write_dockerfile(row, record)
            session.merge(row)
            session.commit()
        return record

    def get_dockerfile(self, dockerfile_id: str) -> DockerfileRecord | None:
        with self._session() as session:
            row = session.get(DockerfileRow, dockerfile_id)
            return _read_dockerfile(row) if row else None

    def list_dockerfiles(
        self,
        *,
        status: str | None = None,
        language: str | None = None,
        model: str | None = None,
        query: str | None = None,
    ) -> list[DockerfileRecord]:
        with self._session() as session:
            rows = session.scalars(
                select(DockerfileRow).order_by(DockerfileRow.created_at.desc())
            ).all()
            projects = {item.id: item for item in session.scalars(select(ProjectRow)).all()}
            records = []
            for row in rows:
                record = _read_dockerfile(row)
                project = (
                    _read_project(projects[row.project_id]) if row.project_id in projects else None
                )
                if matches_history_filters(
                    record, project, status=status, language=language, model=model, query=query
                ):
                    records.append(record)
            return records

    def save_job(self, job: JobRecord) -> JobRecord:
        with self._session() as session:
            row = session.get(JobRow, job.id) or JobRow(id=job.id)
            _write_job(row, job)
            session.merge(row)
            session.commit()
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._session() as session:
            row = session.get(JobRow, job_id)
            return _read_job(row) if row else None

    def update_job(
        self,
        job_id: str,
        *,
        status: str,
        dockerfile_id: str | None = None,
        validation_id: str | None = None,
        error: str | None = None,
        updated_at: datetime | None = None,
    ) -> JobRecord | None:
        with self._session() as session:
            row = session.get(JobRow, job_id)
            if row is None:
                return None
            row.status = status
            if dockerfile_id is not None:
                row.dockerfile_id = dockerfile_id
            if validation_id is not None:
                row.validation_id = validation_id
            if error is not None:
                row.error = error
            row.updated_at = updated_at or utcnow()
            session.commit()
            return _read_job(row)

    def save_validation(self, record: ValidationRecord) -> ValidationRecord:
        with self._session() as session:
            row = session.get(ValidationRow, record.id) or ValidationRow(id=record.id)
            _write_validation(row, record)
            session.merge(row)
            session.commit()
        return record

    def get_validation(self, validation_id: str) -> ValidationRecord | None:
        with self._session() as session:
            row = session.get(ValidationRow, validation_id)
            return _read_validation(row) if row else None

    def list_validations(self, dockerfile_id: str) -> list[ValidationRecord]:
        with self._session() as session:
            rows = session.scalars(
                select(ValidationRow)
                .where(ValidationRow.dockerfile_id == dockerfile_id)
                .order_by(ValidationRow.created_at.desc())
            ).all()
            return [_read_validation(row) for row in rows]

    def list_all_validations(self) -> list[ValidationRecord]:
        with self._session() as session:
            rows = session.scalars(select(ValidationRow)).all()
            return [_read_validation(row) for row in rows]

    def save_repair(self, record: RepairRecord) -> RepairRecord:
        with self._session() as session:
            row = session.get(RepairRow, record.id) or RepairRow(id=record.id)
            _write_repair(row, record)
            session.merge(row)
            session.commit()
        return record

    def get_repair(self, repair_id: str) -> RepairRecord | None:
        with self._session() as session:
            row = session.get(RepairRow, repair_id)
            return _read_repair(row) if row else None

    def list_repairs(self, dockerfile_id: str) -> list[RepairRecord]:
        with self._session() as session:
            rows = session.scalars(
                select(RepairRow)
                .where(
                    (RepairRow.source_dockerfile_id == dockerfile_id)
                    | (RepairRow.result_dockerfile_id == dockerfile_id)
                )
                .order_by(RepairRow.created_at.desc())
            ).all()
            return [_read_repair(row) for row in rows]

    def count_repairs_for_source(self, dockerfile_id: str) -> int:
        return sum(
            1 for item in self.list_all_repairs() if item.source_dockerfile_id == dockerfile_id
        )

    def list_all_repairs(self) -> list[RepairRecord]:
        with self._session() as session:
            rows = session.scalars(select(RepairRow)).all()
            return [_read_repair(row) for row in rows]

    def save_evaluation(self, record: EvaluationRecord) -> EvaluationRecord:
        with self._session() as session:
            row = EvaluationRow(id=record.id)
            _write_evaluation(row, record)
            session.merge(row)
            session.commit()
        return record

    def list_evaluations(self) -> list[EvaluationRecord]:
        with self._session() as session:
            rows = session.scalars(
                select(EvaluationRow).order_by(EvaluationRow.created_at.desc())
            ).all()
            return [_read_evaluation(row) for row in rows]

    def get_setting(self, key: str) -> str | None:
        with self._session() as session:
            row = session.get(SettingRow, key)
            return row.value if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._session() as session:
            row = session.get(SettingRow, key) or SettingRow(key=key, value=value)
            row.value = value
            row.updated_at = utcnow()
            session.merge(row)
            session.commit()

    def list_settings(self) -> dict[str, str]:
        with self._session() as session:
            rows = session.scalars(select(SettingRow)).all()
            return {row.key: row.value for row in rows}


def _write_project(row: ProjectRow, project: ProjectRecord) -> None:
    row.source_type = project.source_type
    row.name = project.name
    row.root_path = project.root_path
    row.language = project.language
    row.framework = project.framework
    row.entry_point = project.entry_point
    row.runtime_version = project.runtime_version
    row.dependencies = list(project.dependencies)
    row.ports = list(project.ports)
    row.build_command = project.build_command
    row.start_command = project.start_command
    row.has_dockerfile = project.has_dockerfile
    row.existing_dockerfile = project.existing_dockerfile
    row.file_tree = list(project.file_tree)
    row.key_files = dict(project.key_files)
    row.created_at = project.created_at


def _read_project(row: ProjectRow) -> ProjectRecord:
    return ProjectRecord(
        id=row.id,
        source_type=row.source_type,
        name=row.name,
        root_path=row.root_path,
        language=row.language,
        framework=row.framework,
        entry_point=row.entry_point,
        runtime_version=row.runtime_version,
        dependencies=list(row.dependencies or []),
        ports=list(row.ports or []),
        build_command=row.build_command,
        start_command=row.start_command,
        has_dockerfile=row.has_dockerfile,
        existing_dockerfile=row.existing_dockerfile,
        file_tree=list(row.file_tree or []),
        key_files=dict(row.key_files or {}),
        created_at=row.created_at,
    )


def _write_dockerfile(row: DockerfileRow, record: DockerfileRecord) -> None:
    row.project_id = record.project_id
    row.dockerfile = record.dockerfile
    row.dockerignore = record.dockerignore
    row.explanation = record.explanation
    row.decisions = list(record.decisions)
    row.model = record.model
    row.instructions = record.instructions
    row.status = record.status
    row.original_dockerfile = record.original_dockerfile
    row.issues = list(record.issues)
    row.parent_id = record.parent_id
    row.repair_attempt = record.repair_attempt
    row.created_at = record.created_at
    row.updated_at = record.updated_at


def _read_dockerfile(row: DockerfileRow) -> DockerfileRecord:
    return DockerfileRecord(
        id=row.id,
        project_id=row.project_id,
        dockerfile=row.dockerfile,
        dockerignore=row.dockerignore,
        explanation=row.explanation,
        decisions=list(row.decisions or []),
        model=row.model,
        instructions=row.instructions,
        status=row.status,
        original_dockerfile=row.original_dockerfile,
        issues=list(row.issues or []),
        parent_id=row.parent_id,
        repair_attempt=row.repair_attempt,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _write_job(row: JobRow, job: JobRecord) -> None:
    row.job_type = job.job_type
    row.status = job.status
    row.dockerfile_id = job.dockerfile_id
    row.validation_id = job.validation_id
    row.error = job.error
    row.created_at = job.created_at
    row.updated_at = job.updated_at


def _read_job(row: JobRow) -> JobRecord:
    return JobRecord(
        id=row.id,
        job_type=row.job_type,
        status=row.status,
        dockerfile_id=row.dockerfile_id,
        validation_id=row.validation_id,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _write_validation(row: ValidationRow, record: ValidationRecord) -> None:
    row.dockerfile_id = record.dockerfile_id
    row.status = record.status
    row.lint = dict(record.lint)
    row.build = dict(record.build)
    row.image_size_bytes = record.image_size_bytes
    row.build_duration_ms = record.build_duration_ms
    row.trivy = dict(record.trivy) if record.trivy is not None else None
    row.startup = dict(record.startup) if record.startup is not None else None
    row.error_log = record.error_log
    row.approved_build = record.approved_build
    row.created_at = record.created_at


def _read_validation(row: ValidationRow) -> ValidationRecord:
    return ValidationRecord(
        id=row.id,
        dockerfile_id=row.dockerfile_id,
        status=row.status,
        lint=dict(row.lint or {}),
        build=dict(row.build or {}),
        image_size_bytes=row.image_size_bytes,
        build_duration_ms=row.build_duration_ms,
        trivy=dict(row.trivy) if row.trivy is not None else None,
        startup=dict(row.startup) if row.startup is not None else None,
        error_log=row.error_log,
        approved_build=row.approved_build,
        created_at=row.created_at,
    )


def _write_repair(row: RepairRow, record: RepairRecord) -> None:
    row.validation_id = record.validation_id
    row.source_dockerfile_id = record.source_dockerfile_id
    row.result_dockerfile_id = record.result_dockerfile_id
    row.attempt = record.attempt
    row.root_cause = record.root_cause
    row.explanation = record.explanation
    row.decisions = list(record.decisions)
    row.status = record.status
    row.created_at = record.created_at


def _read_repair(row: RepairRow) -> RepairRecord:
    return RepairRecord(
        id=row.id,
        validation_id=row.validation_id,
        source_dockerfile_id=row.source_dockerfile_id,
        result_dockerfile_id=row.result_dockerfile_id,
        attempt=row.attempt,
        root_cause=row.root_cause,
        explanation=row.explanation,
        decisions=list(row.decisions or []),
        status=row.status,
        created_at=row.created_at,
    )


def _write_evaluation(row: EvaluationRow, record: EvaluationRecord) -> None:
    row.event = record.event
    row.status = record.status
    row.dockerfile_id = record.dockerfile_id
    row.validation_id = record.validation_id
    row.project_id = record.project_id
    row.language = record.language
    row.framework = record.framework
    row.model = record.model
    row.image_size_bytes = record.image_size_bytes
    row.build_duration_ms = record.build_duration_ms
    row.lint_finding_count = record.lint_finding_count
    row.trivy_finding_count = record.trivy_finding_count
    row.created_at = record.created_at


def _read_evaluation(row: EvaluationRow) -> EvaluationRecord:
    return EvaluationRecord(
        id=row.id,
        event=row.event,
        status=row.status,
        dockerfile_id=row.dockerfile_id,
        validation_id=row.validation_id,
        project_id=row.project_id,
        language=row.language,
        framework=row.framework,
        model=row.model,
        image_size_bytes=row.image_size_bytes,
        build_duration_ms=row.build_duration_ms,
        lint_finding_count=row.lint_finding_count,
        trivy_finding_count=row.trivy_finding_count,
        created_at=row.created_at,
    )
