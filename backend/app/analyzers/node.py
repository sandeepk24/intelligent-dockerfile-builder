"""Detect Node.js applications (Express and common Node servers)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.analyzers.base import Analysis
from app.analyzers.scanner import ScanResult

_PORT_RE = re.compile(r"(?:PORT|port)\s*(?:=|\|\|)\s*[\"']?(\d{2,5})")
_LISTEN_RE = re.compile(r"listen\(\s*(\d{2,5})")


def analyze_node(root: Path, scan: ScanResult) -> Analysis | None:
    package = _load_package_json(scan)
    has_js = any(path.endswith((".js", ".ts", ".mjs", ".cjs")) for path in scan.file_tree)
    if package is None and not has_js:
        return None

    dependencies = _dependency_names(package)
    dep_names = set(dependencies)
    combined = "\n".join(scan.key_files.values()).lower()

    framework = None
    for name in ("express", "nestjs", "fastify", "koa", "next"):
        if name in dep_names or name in combined:
            framework = "express" if name == "express" else name
            break
    if framework == "nestjs":
        framework = "nest"

    entry_point = None
    if package:
        entry_point = package.get("main")
    if not entry_point:
        entry_point = _detect_entry_point(scan)

    scripts = (package or {}).get("scripts", {})
    start_command = scripts.get("start")
    if not start_command and entry_point:
        start_command = f"node {entry_point}"

    ports = _detect_ports(scan) or [3000]
    runtime = None
    if package:
        runtime = (package.get("engines") or {}).get("node")

    return Analysis(
        language="javascript",
        framework=framework,
        entry_point=entry_point,
        runtime_version=str(runtime) if runtime else "20",
        dependencies=dependencies,
        ports=ports,
        build_command="npm ci --omit=dev"
        if "package-lock.json" in scan.file_tree
        else "npm install --omit=dev",
        start_command=start_command,
    )


def _load_package_json(scan: ScanResult) -> dict | None:
    content = scan.key_files.get("package.json")
    if content is None:
        for relative, value in scan.key_files.items():
            if Path(relative).name.lower() == "package.json":
                content = value
                break
    if content is None:
        return None
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _dependency_names(package: dict | None) -> list[str]:
    if not package:
        return []
    names = []
    for key in ("dependencies", "devDependencies"):
        section = package.get(key) or {}
        if isinstance(section, dict):
            names.extend(section.keys())
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def _detect_entry_point(scan: ScanResult) -> str | None:
    for candidate in ("src/index.js", "src/server.js", "index.js", "server.js", "app.js"):
        if candidate in scan.file_tree:
            return candidate
    return None


def _detect_ports(scan: ScanResult) -> list[int]:
    ports: list[int] = []
    for content in scan.key_files.values():
        for match in _PORT_RE.finditer(content):
            ports.append(int(match.group(1)))
        for match in _LISTEN_RE.finditer(content):
            ports.append(int(match.group(1)))
    seen: set[int] = set()
    unique: list[int] = []
    for port in ports:
        if port not in seen:
            seen.add(port)
            unique.append(port)
    return unique
