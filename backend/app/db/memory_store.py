"""Process-local store for analysis results, Dockerfiles, and jobs."""

from __future__ import annotations

from datetime import datetime

from app.models.records import DockerfileRecord, JobRecord, ProjectRecord, utcnow


class MemoryStore:
    """Thread-unsafe in-memory maps; FastAPI async handlers run cooperatively."""

    def __init__(self) -> None:
        self.projects: dict[str, ProjectRecord] = {}
        self.dockerfiles: dict[str, DockerfileRecord] = {}
        self.jobs: dict[str, JobRecord] = {}

    def clear(self) -> None:
        self.projects.clear()
        self.dockerfiles.clear()
        self.jobs.clear()

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
        error: str | None = None,
        updated_at: datetime | None = None,
    ) -> JobRecord | None:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        job.status = status
        if dockerfile_id is not None:
            job.dockerfile_id = dockerfile_id
        if error is not None:
            job.error = error
        job.updated_at = updated_at or utcnow()
        return job


store = MemoryStore()
