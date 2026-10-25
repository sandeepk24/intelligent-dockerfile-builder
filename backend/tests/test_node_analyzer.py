"""Tests for Node.js project detection."""

from pathlib import Path

from app.analyzers.node import analyze_node
from app.analyzers.scanner import scan_project

SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "sample-projects" / "node-express"


def test_detects_express_sample_project():
    scan = scan_project(SAMPLE_ROOT)
    analysis = analyze_node(SAMPLE_ROOT, scan)

    assert analysis is not None
    assert analysis.language == "javascript"
    assert analysis.framework == "express"
    assert analysis.entry_point == "src/index.js"
    assert "express" in analysis.dependencies
    assert 3000 in analysis.ports
    assert analysis.start_command == "node src/index.js"
