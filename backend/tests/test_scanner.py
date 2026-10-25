"""Tests for workspace path safety and project scanning."""

import pytest

from app.analyzers.scanner import scan_project
from app.core.paths import WorkspacePathError, resolve_workspace_path, workspace_root


def test_resolve_workspace_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.workspace_root", str(tmp_path))
    with pytest.raises(WorkspacePathError):
        resolve_workspace_path("../etc/passwd")
    with pytest.raises(WorkspacePathError):
        resolve_workspace_path("/etc/passwd")


def test_resolve_workspace_path_allows_nested_project(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.workspace_root", str(tmp_path))
    project = tmp_path / "python-fastapi"
    project.mkdir()
    resolved = resolve_workspace_path("python-fastapi")
    assert resolved == project.resolve()
    assert workspace_root() == tmp_path.resolve()


def test_scanner_skips_secrets_vendor_and_symlinks(tmp_path):
    project = tmp_path / "app"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text("print('ok')")
    (project / ".env").write_text("SECRET=1")
    (project / "secret.pem").write_text("not-a-key")
    (project / "node_modules").mkdir()
    (project / "node_modules" / "pkg.js").write_text("module.exports = 1")
    (project / "src" / "link.py").symlink_to(project / "src" / "main.py")

    result = scan_project(project)
    assert "src/main.py" in result.file_tree
    assert ".env" not in result.file_tree
    assert "secret.pem" not in result.file_tree
    assert "node_modules/pkg.js" not in result.file_tree
    assert "src/link.py" not in result.file_tree
    assert "src/main.py" in result.key_files


def test_scanner_enforces_file_count_limit(tmp_path):
    project = tmp_path / "many"
    project.mkdir()
    for index in range(5):
        (project / f"file-{index}.txt").write_text("x")

    with pytest.raises(ValueError, match="maximum"):
        scan_project(project, max_files=3)
