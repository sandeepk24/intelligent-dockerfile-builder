"""Process-local store for analysis results, Dockerfiles, jobs, and validations."""

from __future__ import annotations

from datetime import datetime

from app.models.records import (
    DockerfileRecord,
    JobRecord,
    ProjectRecord,
    RepairRecord,
    ValidationRecord,
    utcnow,
)


class MemoryStore:
    """Thread-unsafe in-memory maps; FastAPI async handlers run cooperatively."""

    def __init__(self) -> None:
        self.projects: dict[str, ProjectRecord] = {}
        self.dockerfiles: dict[str, DockerfileRecord] = {}
        self.jobs: dict[str, JobRecord] = {}
        self.validations: dict[str, ValidationRecord] = {}
        self.repairs: dict[str, RepairRecord] = {}

    def clear(self) -> None:
        self.projects.clear()
        self.dockerfiles.clear()
        self.jobs.clear()
        self.validations.clear()
        self.repairs.clear()

    def save_project(self, project: ProjectRecord) -> ProjectRecord:
        self.projects[project.id] = project
        return project

    def get_project(self, project_id: str) -> ProjectRecord | None:
        return self.projects.get(project_id)

    def save_dockerfile(self, record: DockerfileRecord) -> DockerfileRecord:
        self.dockerfiles[record.id] = record
        return record

    def get_dockerfile(self, dockerfile_id: str) -> DockerfileRecord | None:
        return self.dockerfiles.get(dockerfile_id)

    def list_dockerfiles(self) -> list[DockerfileRecord]:
        return sorted(self.dockerfiles.values(), key=lambda item: item.created_at, reverse=True)

    def save_job(self, job: JobRecord) -> JobRecord:
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        return self.jobs.get(job_id)

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
        job = self.jobs.get(job_id)
        if job is None:
            return None
        job.status = status
        if dockerfile_id is not None:
            job.dockerfile_id = dockerfile_id
        if validation_id is not None:
            job.validation_id = validation_id
        if error is not None:
            job.error = error
        job.updated_at = updated_at or utcnow()
        return job

    def save_validation(self, record: ValidationRecord) -> ValidationRecord:
        self.validations[record.id] = record
        return record

    def get_validation(self, validation_id: str) -> ValidationRecord | None:
        return self.validations.get(validation_id)

    def list_validations(self, dockerfile_id: str) -> list[ValidationRecord]:
        items = [item for item in self.validations.values() if item.dockerfile_id == dockerfile_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def list_all_validations(self) -> list[ValidationRecord]:
        return list(self.validations.values())

    def save_repair(self, record: RepairRecord) -> RepairRecord:
        self.repairs[record.id] = record
        return record

    def get_repair(self, repair_id: str) -> RepairRecord | None:
        return self.repairs.get(repair_id)

    def list_repairs(self, dockerfile_id: str) -> list[RepairRecord]:
        items = [
            item
            for item in self.repairs.values()
            if item.source_dockerfile_id == dockerfile_id
            or item.result_dockerfile_id == dockerfile_id
        ]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def count_repairs_for_source(self, dockerfile_id: str) -> int:
        return sum(
            1 for item in self.repairs.values() if item.source_dockerfile_id == dockerfile_id
        )


store = MemoryStore()
