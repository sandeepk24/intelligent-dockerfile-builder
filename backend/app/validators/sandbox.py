"""Prepare an isolated build context from an analyzed project."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.models.records import DockerfileRecord, ProjectRecord

logger = get_logger(__name__)


def prepare_build_context(
    project: ProjectRecord,
    dockerfile_record: DockerfileRecord,
) -> Path:
    """Copy only scanned project files into a throwaway sandbox directory."""
    sandbox_root = Path(settings.docker_sandbox_dir).expanduser().resolve()
    sandbox_root.mkdir(parents=True, exist_ok=True)
    context = sandbox_root / uuid4().hex
    context.mkdir(parents=True, exist_ok=False)

    source_root = Path(project.root_path) if project.root_path else None
    if source_root and source_root.is_dir() and not source_root.is_symlink():
        for relative in project.file_tree:
            src = (source_root / relative).resolve()
            if source_root.resolve() not in src.parents and src != source_root.resolve():
                continue
            if src.is_symlink() or not src.is_file():
                continue
            dest = context / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    (context / "Dockerfile").write_text(dockerfile_record.dockerfile)
    if dockerfile_record.dockerignore:
        (context / ".dockerignore").write_text(dockerfile_record.dockerignore)
    return context


def cleanup_context(context: Path) -> None:
    try:
        shutil.rmtree(context, ignore_errors=True)
    except OSError as exc:
        logger.warning("Could not remove sandbox %s: %s", context, exc)
