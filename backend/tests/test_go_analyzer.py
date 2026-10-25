"""Tests for Go project detection."""

from pathlib import Path

from app.analyzers.detector import detect_project
from app.analyzers.go import analyze_go
from app.analyzers.scanner import scan_project

SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "sample-projects" / "go-api"


def test_detects_go_sample_project():
    scan = scan_project(SAMPLE_ROOT)
    analysis = analyze_go(SAMPLE_ROOT, scan)

    assert analysis is not None
    assert analysis.language == "go"
    assert analysis.entry_point == "main.go"
    assert analysis.runtime_version == "1.22"
    assert 8080 in analysis.ports


def test_detector_selects_go_for_sample():
    scan = scan_project(SAMPLE_ROOT)
    analysis = detect_project(SAMPLE_ROOT, scan)
    assert analysis.language == "go"
