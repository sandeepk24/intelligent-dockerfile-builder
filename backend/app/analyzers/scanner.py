"""Scan a project tree while skipping secrets, VCS, and vendor directories."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from app.analyzers.exclusions import is_excluded_dir, is_excluded_file, is_key_file, is_text_file
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_FILE_BYTES = 16_384


@dataclass
class ScanResult:
    root: Path
    file_tree: list[str] = field(default_factory=list)
    key_files: dict[str, str] = field(default_factory=dict)
    existing_dockerfile: str | None = None


def scan_project(root: Path, *, max_files: int | None = None) -> ScanResult:
    """Walk `root` without following symlinks and collect a sanitized file view."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Project root must be a real directory")

    limit = max_files or settings.max_file_count
    result = ScanResult(root=root)
    file_count = 0

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if not is_excluded_dir(name) and not (current_path / name).is_symlink()
        )
        for name in sorted(filenames):
            path = current_path / name
            if path.is_symlink() or is_excluded_file(path) or not path.is_file():
                continue

            file_count += 1
            if file_count > limit:
                raise ValueError(f"Project exceeds the maximum of {limit} files")

            relative = path.relative_to(root).as_posix()
            result.file_tree.append(relative)

            if not is_text_file(path):
                continue
            if is_key_file(path) or path.name.lower() == "dockerfile":
                content = _read_text(path)
                result.key_files[relative] = content
                if path.name.lower() == "dockerfile" and result.existing_dockerfile is None:
                    result.existing_dockerfile = content

    result.file_tree.sort()
    return result


def _read_text(path: Path) -> str:
    try:
        data = path.read_bytes()[:MAX_FILE_BYTES]
    except OSError as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return ""
    return data.decode("utf-8", errors="replace")
