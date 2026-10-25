"""Detect Python applications (FastAPI, Flask, Django)."""

from __future__ import annotations

import re
from pathlib import Path

from app.analyzers.base import Analysis
from app.analyzers.scanner import ScanResult

_REQ_NAME_RE = re.compile(r"^([A-Za-z0-9_.-]+)")
_PORT_RE = re.compile(r"(?:port|PORT)\s*=\s*[\"']?(\d{2,5})")
_LISTEN_RE = re.compile(r"uvicorn\.run\([^)]*port\s*=\s*(\d{2,5})")


def analyze_python(root: Path, scan: ScanResult) -> Analysis | None:
    names = {Path(path).name.lower() for path in scan.file_tree}
    has_py = any(path.endswith(".py") for path in scan.file_tree)
    manifest_hit = bool(
        names
        & {
            "requirements.txt",
            "pyproject.toml",
            "pipfile",
            "setup.py",
            "setup.cfg",
            "manage.py",
        }
    )
    if not has_py and not manifest_hit:
        return None

    dependencies = _collect_dependencies(scan)
    dep_names = {dep.lower() for dep in dependencies}
    combined = "\n".join(scan.key_files.values()).lower()

    framework = None
    ports = [8000]
    start_command = None
    if "fastapi" in dep_names or "fastapi" in combined:
        framework = "fastapi"
        ports = [8000]
        start_command = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    elif "django" in dep_names or "django" in combined or "manage.py" in names:
        framework = "django"
        ports = [8000]
        start_command = "python manage.py runserver 0.0.0.0:8000"
    elif "flask" in dep_names or "flask" in combined:
        framework = "flask"
        ports = [5000]
        start_command = "flask run --host 0.0.0.0 --port 5000"

    entry_point = _detect_entry_point(scan, framework)
    if framework == "fastapi" and entry_point:
        module = entry_point.replace("/", ".").removesuffix(".py")
        start_command = f"uvicorn {module}:app --host 0.0.0.0 --port 8000"

    detected_ports = _detect_ports(scan)
    if detected_ports:
        ports = detected_ports

    return Analysis(
        language="python",
        framework=framework,
        entry_point=entry_point,
        runtime_version=_detect_python_version(scan),
        dependencies=dependencies,
        ports=ports,
        build_command="pip install --no-cache-dir -r requirements.txt",
        start_command=start_command,
    )


def _collect_dependencies(scan: ScanResult) -> list[str]:
    deps: list[str] = []
    for relative, content in scan.key_files.items():
        name = Path(relative).name.lower()
        if name == "requirements.txt":
            deps.extend(_parse_requirements(content))
        elif name == "pyproject.toml":
            deps.extend(_parse_pyproject(content))
    return _unique(deps)


def _parse_requirements(content: str) -> list[str]:
    names: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        match = _REQ_NAME_RE.match(stripped)
        if match:
            names.append(match.group(1))
    return names


def _parse_pyproject(content: str) -> list[str]:
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        return []

    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return []

    project = data.get("project", {})
    raw = project.get("dependencies", [])
    names: list[str] = []
    for item in raw:
        match = _REQ_NAME_RE.match(str(item).strip())
        if match:
            names.append(match.group(1))
    return names


def _detect_entry_point(scan: ScanResult, framework: str | None) -> str | None:
    preferred = [
        "app/main.py",
        "main.py",
        "app.py",
        "manage.py",
        "wsgi.py",
        "asgi.py",
        "src/main.py",
    ]
    tree = set(scan.file_tree)
    for candidate in preferred:
        if candidate in tree:
            return candidate
    if framework == "django":
        for path in scan.file_tree:
            if path.endswith("manage.py"):
                return path
    for path in scan.file_tree:
        if path.endswith(".py") and Path(path).stem in {"main", "app", "wsgi", "asgi"}:
            return path
    return None


def _detect_python_version(scan: ScanResult) -> str:
    for relative, content in scan.key_files.items():
        name = Path(relative).name.lower()
        if name in {".python-version", "runtime.txt"}:
            match = re.search(r"3\.\d+", content)
            if match:
                return match.group(0)
        if name == "pyproject.toml":
            match = re.search(r"requires-python\s*=\s*[\"']>=?\s*(3\.\d+)", content)
            if match:
                return match.group(1)
    return "3.12"


def _detect_ports(scan: ScanResult) -> list[int]:
    ports: list[int] = []
    for content in scan.key_files.values():
        for match in _PORT_RE.finditer(content):
            ports.append(int(match.group(1)))
        for match in _LISTEN_RE.finditer(content):
            ports.append(int(match.group(1)))
    return _unique(ports)


def _unique(values: list) -> list:
    seen: set = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
