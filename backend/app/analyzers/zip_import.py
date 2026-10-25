"""Validate and extract uploaded ZIP archives as untrusted input."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_COMPRESSION_RATIO = 20
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
CHUNK_SIZE = 65_536


class ZipSecurityError(ValueError):
    """Raised when a ZIP archive fails security validation."""


def extract_zip(archive_path: Path, destination: Path) -> Path:
    """Extract a ZIP into `destination` after security checks.

    Returns the project root, unwrapping a single top-level directory when present.
    """
    max_upload_bytes = settings.max_upload_size_mb * 1024 * 1024
    if archive_path.stat().st_size > max_upload_bytes:
        raise ZipSecurityError("ZIP exceeds the configured upload size limit")
    if not zipfile.is_zipfile(archive_path):
        raise ZipSecurityError("Uploaded file is not a valid ZIP archive")

    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        _validate_archive(members)
        for info in members:
            _extract_member(archive, info, destination)

    return _unwrap_single_root(destination)


def _validate_archive(members: list[zipfile.ZipInfo]) -> None:
    if len(members) > settings.max_file_count:
        raise ZipSecurityError("ZIP contains too many files")

    total_uncompressed = 0
    for info in members:
        _validate_member(info)
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ZipSecurityError("ZIP uncompressed size exceeds the allowed limit")


def _validate_member(info: zipfile.ZipInfo) -> None:
    name = info.filename.replace("\\", "/")
    if name.startswith("/") or name.startswith("\\") or Path(name).is_absolute():
        raise ZipSecurityError("ZIP contains an absolute path")
    parts = Path(name).parts
    if ".." in parts:
        raise ZipSecurityError("ZIP contains a path traversal entry")
    if _is_symlink(info):
        raise ZipSecurityError("ZIP contains a symbolic link")
    if info.file_size > MAX_UNCOMPRESSED_BYTES:
        raise ZipSecurityError("ZIP member is too large")
    if (
        info.compress_size
        and info.file_size > 1024 * 1024
        and info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO
    ):
        raise ZipSecurityError("ZIP compression ratio is too high")


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    unix_mode = info.external_attr >> 16
    return bool(unix_mode) and stat.S_ISLNK(unix_mode)


def _extract_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, destination: Path) -> None:
    relative = Path(info.filename.replace("\\", "/"))
    if not info.filename or info.is_dir() or str(relative).endswith("/"):
        return

    target = (destination / relative).resolve()
    if destination.resolve() not in target.parents and target != destination.resolve():
        raise ZipSecurityError("ZIP extract escaped the destination directory")

    target.parent.mkdir(parents=True, exist_ok=True)
    copied = 0
    with archive.open(info) as source, target.open("wb") as output:
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            copied += len(chunk)
            if copied > info.file_size:
                raise ZipSecurityError("ZIP member exceeded its declared size")
            output.write(chunk)


def _unwrap_single_root(destination: Path) -> Path:
    entries = [path for path in destination.iterdir() if path.name not in {"__MACOSX", ".DS_Store"}]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return destination
