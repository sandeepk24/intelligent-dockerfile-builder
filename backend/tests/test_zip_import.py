"""Tests for ZIP upload security checks."""

import stat
import zipfile
from pathlib import Path

import pytest

from app.analyzers.zip_import import ZipSecurityError, extract_zip


def _write_zip(path: Path, entries: dict[str, bytes], *, symlink_name: str | None = None) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
        if symlink_name:
            info = zipfile.ZipInfo(symlink_name)
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o644) << 16
            archive.writestr(info, b"../secret")
    return path


def test_extracts_valid_zip_and_unwraps_root(tmp_path):
    archive = _write_zip(
        tmp_path / "app.zip",
        {
            "demo/app.py": b"print('ok')",
            "demo/requirements.txt": b"fastapi\n",
        },
    )
    dest = tmp_path / "out"
    root = extract_zip(archive, dest)
    assert (root / "app.py").read_text() == "print('ok')"
    assert root.name == "demo"


def test_rejects_path_traversal(tmp_path):
    archive = _write_zip(tmp_path / "bad.zip", {"../evil.py": b"nope"})
    with pytest.raises(ZipSecurityError, match="traversal"):
        extract_zip(archive, tmp_path / "out")


def test_rejects_symlink_member(tmp_path):
    archive = _write_zip(tmp_path / "link.zip", {"ok.txt": b"ok"}, symlink_name="link")
    with pytest.raises(ZipSecurityError, match="symbolic link"):
        extract_zip(archive, tmp_path / "out")


def test_rejects_oversize_upload(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.max_upload_size_mb", 0)
    archive = _write_zip(tmp_path / "big.zip", {"a.txt": b"hello world"})
    with pytest.raises(ZipSecurityError, match="upload size"):
        extract_zip(archive, tmp_path / "out")
