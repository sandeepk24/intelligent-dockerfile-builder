"""Tests for .dockerignore generation."""

from app.analyzers.base import Analysis
from app.generators.dockerignore import generate_dockerignore


def test_python_dockerignore_excludes_venv_and_secrets():
    content = generate_dockerignore(Analysis(language="python", framework="fastapi"))
    assert ".env" in content
    assert ".venv" in content
    assert "node_modules" not in content


def test_node_dockerignore_excludes_node_modules():
    content = generate_dockerignore(Analysis(language="javascript", framework="express"))
    assert "node_modules" in content
    assert ".env" in content
