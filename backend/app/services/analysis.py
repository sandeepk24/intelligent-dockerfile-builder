"""Orchestrate project analysis for workspace directories and ZIP uploads."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.analyzers.detector import detect_project
from app.analyzers.dockerfile_review import issues_to_dicts, review_dockerfile
from app.analyzers.scanner import scan_project
from app.analyzers.zip_import import extract_zip
from app.core.paths import resolve_workspace_path, workspace_root
from app.db.memory_store import store
from app.models.records import ProjectRecord
from app.schemas.dockerfile import DockerfileIssueResponse
from app.schemas.project import ProjectAnalysisResponse, WorkspaceProject


def list_workspace_projects() -> list[WorkspaceProject]:
    root = workspace_root()
    projects: list[WorkspaceProject] = []
    for entry in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if entry.name.startswith(".") or entry.is_symlink() or not entry.is_dir():
            continue
        projects.append(
            WorkspaceProject(
                name=entry.name,
                path=entry.name,
                has_dockerfile=(entry / "Dockerfile").is_file(),
            )
        )
    return projects


def analyze_directory(relative_path: str) -> ProjectRecord:
    root = resolve_workspace_path(relative_path)
    if not root.is_dir():
        raise FileNotFoundError(f"Workspace project not found: {relative_path}")
    return _analyze_root(root, source_type="directory", name=root.name)


def analyze_dockerfile_text(content: str, name: str | None = None) -> ProjectRecord:
    dockerfile = content.strip()
    if not dockerfile or not any(
        line.strip().upper().startswith("FROM") for line in dockerfile.splitlines()
    ):
        raise ValueError("Provided text is not a Dockerfile (missing FROM)")
    language = _guess_language(dockerfile)
    record = ProjectRecord(
        id=str(uuid4()),
        source_type="dockerfile",
        name=name or "pasted-dockerfile",
        root_path="",
        language=language,
        has_dockerfile=True,
        existing_dockerfile=dockerfile + ("\n" if not dockerfile.endswith("\n") else ""),
        file_tree=["Dockerfile"],
        key_files={"Dockerfile": dockerfile[:16_384]},
    )
    return store.save_project(record)


def analyze_zip_bytes(content: bytes, filename: str) -> ProjectRecord:
    upload_id = uuid4().hex
    upload_dir = workspace_root() / ".uploads" / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    archive_path = upload_dir / (filename or "project.zip")
    archive_path.write_bytes(content)
    extracted = extract_zip(archive_path, upload_dir / "src")
    return _analyze_root(
        extracted,
        source_type="zip",
        name=Path(filename).stem or extracted.name,
    )


def get_project(project_id: str) -> ProjectRecord | None:
    return store.get_project(project_id)


def to_analysis_response(project: ProjectRecord) -> ProjectAnalysisResponse:
    return ProjectAnalysisResponse(
        project_id=project.id,
        name=project.name,
        source_type=project.source_type,
        language=project.language,
        framework=project.framework,
        entry_point=project.entry_point,
        runtime_version=project.runtime_version,
        dependencies=project.dependencies,
        ports=project.ports,
        build_command=project.build_command,
        start_command=project.start_command,
        has_dockerfile=project.has_dockerfile,
        existing_dockerfile=project.existing_dockerfile,
        dockerfile_issues=[
            DockerfileIssueResponse.model_validate(item)
            for item in issues_to_dicts(
                review_dockerfile(project.existing_dockerfile, ports=project.ports)
            )
        ]
        if project.existing_dockerfile
        else [],
        file_tree=project.file_tree,
        created_at=project.created_at,
    )


def _analyze_root(root: Path, *, source_type: str, name: str) -> ProjectRecord:
    scan = scan_project(root)
    analysis = detect_project(root, scan)
    record = ProjectRecord(
        id=str(uuid4()),
        source_type=source_type,
        name=name,
        root_path=str(root),
        language=analysis.language,
        framework=analysis.framework,
        entry_point=analysis.entry_point,
        runtime_version=analysis.runtime_version,
        dependencies=analysis.dependencies,
        ports=analysis.ports,
        build_command=analysis.build_command,
        start_command=analysis.start_command,
        has_dockerfile=scan.existing_dockerfile is not None,
        existing_dockerfile=scan.existing_dockerfile,
        file_tree=scan.file_tree,
        key_files=scan.key_files,
    )
    return store.save_project(record)


def _guess_language(dockerfile: str) -> str | None:
    lowered = dockerfile.lower()
    if "python" in lowered:
        return "python"
    if "node" in lowered or "npm" in lowered:
        return "javascript"
    if "golang" in lowered or "from go:" in lowered:
        return "go"
    return None
