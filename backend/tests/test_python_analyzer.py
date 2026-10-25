"""Tests for Python project detection."""

from pathlib import Path

from app.analyzers.python import analyze_python
from app.analyzers.scanner import scan_project

SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "sample-projects" / "python-fastapi"


def test_detects_fastapi_sample_project():
    scan = scan_project(SAMPLE_ROOT)
    analysis = analyze_python(SAMPLE_ROOT, scan)

    assert analysis is not None
    assert analysis.language == "python"
    assert analysis.framework == "fastapi"
    assert analysis.entry_point == "app/main.py"
    assert "fastapi" in [dep.lower() for dep in analysis.dependencies]
    assert 8000 in analysis.ports
    assert analysis.start_command and "uvicorn" in analysis.start_command
