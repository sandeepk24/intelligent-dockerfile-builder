"""Select the best language analyzer for a scanned project."""

from pathlib import Path

from app.analyzers.base import Analysis
from app.analyzers.go import analyze_go
from app.analyzers.node import analyze_node
from app.analyzers.python import analyze_python
from app.analyzers.scanner import ScanResult


def detect_project(root: Path, scan: ScanResult) -> Analysis:
    """Run language analyzers in priority order and return the first match."""
    for analyzer in (analyze_python, analyze_node, analyze_go):
        result = analyzer(root, scan)
        if result is not None:
            return result
    return Analysis(language="unknown")
