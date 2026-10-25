"""Detect Go applications."""

from __future__ import annotations

import re
from pathlib import Path

from app.analyzers.base import Analysis
from app.analyzers.scanner import ScanResult

_GO_VERSION_RE = re.compile(r"^go\s+(\d+\.\d+)", re.MULTILINE)
_LISTEN_RE = re.compile(r'ListenAndServe\(\s*":(\d{2,5})"')
_PORT_RE = re.compile(r"(?:PORT|port)\s*[:=]\s*[\"']?(\d{2,5})")


def analyze_go(root: Path, scan: ScanResult) -> Analysis | None:
    names = {Path(path).name.lower() for path in scan.file_tree}
    has_go = any(path.endswith(".go") for path in scan.file_tree)
    if "go.mod" not in names and not has_go:
        return None

    go_mod = _find_file(scan, "go.mod")
    runtime = "1.22"
    if go_mod:
        match = _GO_VERSION_RE.search(go_mod)
        if match:
            runtime = match.group(1)

    entry_point = "main.go" if "main.go" in scan.file_tree else _first_main(scan)
    ports = _detect_ports(scan) or [8080]
    binary = Path(root).name.replace("_", "-")

    return Analysis(
        language="go",
        framework="go",
        entry_point=entry_point,
        runtime_version=runtime,
        dependencies=_parse_go_mod_requires(go_mod or ""),
        ports=ports,
        build_command=f"CGO_ENABLED=0 go build -o /out/{binary} .",
        start_command=f"/{binary}",
    )


def _find_file(scan: ScanResult, name: str) -> str | None:
    for relative, content in scan.key_files.items():
        if Path(relative).name.lower() == name:
            return content
    return None


def _first_main(scan: ScanResult) -> str | None:
    for path in scan.file_tree:
        if Path(path).name == "main.go":
            return path
    return None


def _parse_go_mod_requires(content: str) -> list[str]:
    deps: list[str] = []
    in_block = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        if stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                deps.append(parts[1])
        elif in_block and stripped and not stripped.startswith("//"):
            deps.append(stripped.split()[0])
    return deps


def _detect_ports(scan: ScanResult) -> list[int]:
    ports: list[int] = []
    for content in scan.key_files.values():
        for regex in (_LISTEN_RE, _PORT_RE):
            for match in regex.finditer(content):
                ports.append(int(match.group(1)))
    seen: set[int] = set()
    unique: list[int] = []
    for port in ports:
        if port not in seen:
            seen.add(port)
            unique.append(port)
    return unique
