"""Deterministic review of an existing Dockerfile.

These checks run without an LLM so users see issues immediately.
The optimizer later uses the same findings as trusted context.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

_FROM_RE = re.compile(r"^FROM\s+(\S+)", re.IGNORECASE)
_USER_RE = re.compile(r"^USER\s+(\S+)", re.IGNORECASE)
_EXPOSE_RE = re.compile(r"^EXPOSE\s+(.+)$", re.IGNORECASE)
_SECRET_COPY_RE = re.compile(
    r"^(?:COPY|ADD)\s+.*(?:\.env|\.pem|\.key|id_rsa|credentials\.json|secrets\.(?:ya?ml))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DockerfileIssue:
    code: str
    severity: str
    title: str
    detail: str
    suggestion: str
    line: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def review_dockerfile(content: str, *, ports: list[int] | None = None) -> list[DockerfileIssue]:
    """Return ordered issues found in Dockerfile text."""
    if not content or not content.strip():
        return [
            DockerfileIssue(
                code="empty",
                severity="high",
                title="Dockerfile is empty",
                detail="No instructions were provided.",
                suggestion="Paste or generate a Dockerfile that starts with FROM.",
            )
        ]

    lines = content.splitlines()
    issues: list[DockerfileIssue] = []
    issues.extend(_check_from(lines))
    issues.extend(_check_user(lines))
    issues.extend(_check_add_and_copy(lines))
    issues.extend(_check_package_installs(lines))
    issues.extend(_check_secrets(lines))
    issues.extend(_check_workdir_and_command(lines))
    issues.extend(_check_expose(lines, ports or []))
    issues.extend(_check_privileged_patterns(lines))
    return issues


def issues_to_dicts(issues: list[DockerfileIssue]) -> list[dict]:
    return [issue.to_dict() for issue in issues]


def _check_from(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    found_from = False
    for number, raw in _instructions(lines):
        match = _FROM_RE.match(raw)
        if not match:
            continue
        found_from = True
        image = match.group(1)
        name = image.split("/")[-1]
        if name.lower() in {"scratch"}:
            continue
        if ":" not in name:
            issues.append(
                DockerfileIssue(
                    code="unpinned-base-image",
                    severity="high",
                    title="Base image is not tagged",
                    detail=f"Line {number} uses `{image}` without a version tag, so builds are not reproducible.",
                    suggestion="Pin an official image tag such as `python:3.12-slim` or `node:20-alpine`.",
                    line=number,
                )
            )
        elif name.lower().endswith(":latest") or ":latest" in image.lower():
            issues.append(
                DockerfileIssue(
                    code="latest-tag",
                    severity="high",
                    title="Base image uses the latest tag",
                    detail=f"Line {number} uses `{image}`. `latest` moves and is a common production footgun.",
                    suggestion="Replace `:latest` with a specific version, preferably a slim or distroless variant.",
                    line=number,
                )
            )
    if not found_from:
        issues.append(
            DockerfileIssue(
                code="missing-from",
                severity="high",
                title="Missing FROM instruction",
                detail="A Dockerfile must start from a base image.",
                suggestion="Add a pinned FROM line, for example `FROM python:3.12-slim`.",
            )
        )
    return issues


def _check_user(lines: list[str]) -> list[DockerfileIssue]:
    last_user: tuple[int, str] | None = None
    for number, raw in _instructions(lines):
        match = _USER_RE.match(raw)
        if match:
            last_user = (number, match.group(1))
    if last_user is None:
        return [
            DockerfileIssue(
                code="runs-as-root",
                severity="high",
                title="Container runs as root",
                detail="No USER instruction was found, so the process inherits root from the base image.",
                suggestion="Create a non-root user and add `USER appuser` before CMD/ENTRYPOINT.",
            )
        ]
    number, name = last_user
    if name in {"0", "root"}:
        return [
            DockerfileIssue(
                code="explicit-root-user",
                severity="high",
                title="USER is set to root",
                detail=f"Line {number} sets `USER {name}`.",
                suggestion="Switch to a non-root user after installing packages.",
                line=number,
            )
        ]
    return []


def _check_add_and_copy(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    copies: list[tuple[int, str]] = []
    for number, raw in _instructions(lines):
        upper = raw.upper()
        if upper.startswith("ADD "):
            issues.append(
                DockerfileIssue(
                    code="add-instead-of-copy",
                    severity="medium",
                    title="ADD used for local files",
                    detail=f"Line {number} uses ADD, which unpacks archives and accepts remote URLs.",
                    suggestion="Use COPY for local source. Reserve ADD for explicit remote/archive cases.",
                    line=number,
                )
            )
        if upper.startswith("COPY ") or upper.startswith("ADD "):
            copies.append((number, raw))
    if copies:
        first_line, first_raw = copies[0]
        if re.search(r"COPY\s+(?:--from=\S+\s+)?\.\s", first_raw, re.IGNORECASE) or re.search(
            r"ADD\s+\.\s", first_raw, re.IGNORECASE
        ):
            issues.append(
                DockerfileIssue(
                    code="copy-context-too-early",
                    severity="medium",
                    title="Full build context copied before dependencies",
                    detail=f"Line {first_line} copies the entire context first, which breaks dependency layer caching.",
                    suggestion="Copy only the lockfile/manifest, install dependencies, then copy application source.",
                    line=first_line,
                )
            )
    return issues


def _check_package_installs(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    for number, raw in _instructions(lines):
        lower = raw.lower()
        if "pip install" in lower and "--no-cache-dir" not in lower:
            issues.append(
                DockerfileIssue(
                    code="pip-cache",
                    severity="medium",
                    title="pip install keeps the download cache",
                    detail=f"Line {number} runs pip without `--no-cache-dir`.",
                    suggestion="Use `pip install --no-cache-dir` to shrink the image.",
                    line=number,
                )
            )
        if (
            "apt-get install" in lower or "apt install" in lower
        ) and "rm -rf /var/lib/apt/lists" not in lower:
            issues.append(
                DockerfileIssue(
                    code="apt-lists",
                    severity="medium",
                    title="apt package lists are not cleaned",
                    detail=f"Line {number} installs apt packages without deleting `/var/lib/apt/lists`.",
                    suggestion="Chain `rm -rf /var/lib/apt/lists/*` in the same RUN instruction.",
                    line=number,
                )
            )
        if (
            "npm install" in lower
            and "npm ci" not in lower
            and "--omit=dev" not in lower
            and "--only=production" not in lower
        ):
            issues.append(
                DockerfileIssue(
                    code="npm-dev-deps",
                    severity="low",
                    title="npm install may include development dependencies",
                    detail=f"Line {number} uses npm install rather than a production install.",
                    suggestion="Prefer `npm ci --omit=dev` when a lockfile is present.",
                    line=number,
                )
            )
        if "curl" in lower and "|" in raw and "sh" in lower:
            issues.append(
                DockerfileIssue(
                    code="curl-pipe-shell",
                    severity="high",
                    title="Remote script piped to a shell",
                    detail=f"Line {number} pipes a download into sh/bash.",
                    suggestion="Download, verify checksums, then install from a local file.",
                    line=number,
                )
            )
    return issues


def _check_secrets(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    for number, raw in _instructions(lines):
        if _SECRET_COPY_RE.search(raw):
            issues.append(
                DockerfileIssue(
                    code="copies-secrets",
                    severity="high",
                    title="Secret file copied into the image",
                    detail=f"Line {number} copies a credential-like file into the image layers.",
                    suggestion="Keep secrets in runtime env or a secret store. Add the path to `.dockerignore`.",
                    line=number,
                )
            )
        if re.search(r"(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*\S+", raw, re.IGNORECASE):
            issues.append(
                DockerfileIssue(
                    code="hardcoded-secret",
                    severity="high",
                    title="Possible secret hardcoded in the Dockerfile",
                    detail=f"Line {number} looks like an embedded credential.",
                    suggestion="Pass secrets at runtime with ENV from the orchestrator, never bake them into layers.",
                    line=number,
                )
            )
    return issues


def _check_workdir_and_command(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    has_workdir = False
    has_command = False
    for _number, raw in _instructions(lines):
        upper = raw.upper()
        if upper.startswith("WORKDIR "):
            has_workdir = True
        if upper.startswith("CMD ") or upper.startswith("ENTRYPOINT "):
            has_command = True
    if not has_workdir:
        issues.append(
            DockerfileIssue(
                code="missing-workdir",
                severity="low",
                title="WORKDIR is not set",
                detail="Commands run from `/` unless WORKDIR is defined.",
                suggestion="Set `WORKDIR /app` (or a similar application directory).",
            )
        )
    if not has_command:
        issues.append(
            DockerfileIssue(
                code="missing-cmd",
                severity="high",
                title="No CMD or ENTRYPOINT",
                detail="The image has no default process to start.",
                suggestion="Add a CMD that launches the detected application entry point.",
            )
        )
    return issues


def _check_expose(lines: list[str], ports: list[int]) -> list[DockerfileIssue]:
    exposed: set[int] = set()
    for _number, raw in _instructions(lines):
        match = _EXPOSE_RE.match(raw)
        if not match:
            continue
        for token in match.group(1).split():
            try:
                exposed.add(int(token.split("/")[0]))
            except ValueError:
                continue
    if ports and not exposed.intersection(ports):
        expected = ", ".join(str(port) for port in ports)
        return [
            DockerfileIssue(
                code="missing-expose",
                severity="low",
                title="Detected ports are not exposed",
                detail=f"The application appears to listen on {expected}, but EXPOSE does not match.",
                suggestion=f"Add `EXPOSE {ports[0]}` for documentation and tooling.",
            )
        ]
    return []


def _check_privileged_patterns(lines: list[str]) -> list[DockerfileIssue]:
    issues: list[DockerfileIssue] = []
    for number, raw in _instructions(lines):
        if re.search(r"\bsudo\b", raw, re.IGNORECASE):
            issues.append(
                DockerfileIssue(
                    code="sudo",
                    severity="medium",
                    title="sudo used inside the image",
                    detail=f"Line {number} calls sudo, which is unnecessary in a container and expands the attack surface.",
                    suggestion="Install packages as root in a build stage, then drop to a non-root USER.",
                    line=number,
                )
            )
    return issues


def _instructions(lines: list[str]) -> list[tuple[int, str]]:
    """Yield physical line numbers and instruction text, joining backslash continuations."""
    results: list[tuple[int, str]] = []
    buffer = ""
    start = 0
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not buffer:
            start = index
        if stripped.endswith("\\"):
            buffer += stripped[:-1].rstrip() + " "
            continue
        buffer += stripped
        results.append((start, buffer))
        buffer = ""
    if buffer:
        results.append((start, buffer))
    return results
