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
    issues.extend(_check_base_variant(lines))
    issues.extend(_check_sdk_final_image(lines))
    issues.extend(_check_build_dependencies(lines))
    issues.extend(_check_user(lines))
    issues.extend(_check_add_and_copy(lines))
    issues.extend(_check_package_installs(lines))
    issues.extend(_check_split_apt(lines))
    issues.extend(_check_apt_recommends(lines))
    issues.extend(_check_consecutive_runs(lines))
    issues.extend(_check_secrets(lines))
    issues.extend(_check_workdir_and_command(lines))
    issues.extend(_check_exec_form(lines))
    issues.extend(_check_expose(lines, ports or []))
    issues.extend(_check_healthcheck(lines, ports or []))
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


# Official images that publish a smaller variant. The tag is the part after ':'.
_SMALLER_BASE_SUGGESTIONS = {
    "python": "python:3.12-slim",
    "node": "node:22-alpine",
    "ruby": "ruby:3.3-slim",
    "golang": "golang:1.23-alpine",
    "openjdk": "eclipse-temurin:21-jre-alpine",
    "eclipse-temurin": "eclipse-temurin:21-jre-alpine",
}
_SMALL_TAG_MARKERS = ("slim", "alpine", "distroless")
_RUNTIME_TAG_MARKERS = ("jre",)


def _check_base_variant(lines: list[str]) -> list[DockerfileIssue]:
    """Flag a pinned full official image when a smaller variant exists.

    Untagged images and `:latest` are already reported by `_check_from`.
    This check only fires when the tag is specific but still a full image,
    for example `python:3.12` or `python:3.12-bookworm`.
    """
    stage = _final_stage(lines)
    from_instruction = _first_from(stage)
    if from_instruction is None:
        return []
    number, raw = from_instruction
    image = _image_reference(raw).split("@", 1)[0]
    name = image.split("/")[-1]
    if ":" not in name:
        return []
    repository, tag = name.rsplit(":", 1)
    family = repository.lower()
    if family not in _SMALLER_BASE_SUGGESTIONS or tag.lower() == "latest":
        return []
    tag_parts = set(tag.lower().split("-"))
    if tag_parts.intersection(_SMALL_TAG_MARKERS) or tag_parts.intersection(_RUNTIME_TAG_MARKERS):
        return []
    suggestion = _SMALLER_BASE_SUGGESTIONS[family]
    return [
        DockerfileIssue(
            code="full-base-image",
            severity="medium",
            title="Final base image is larger than necessary",
            detail=(
                f"Line {number} uses `{image}`. That tag includes build tooling and "
                "extra OS packages that the running process does not need."
            ),
            suggestion=f"Prefer a smaller official variant such as `{suggestion}`.",
            line=number,
        )
    ]


_SDK_RUNTIMES = {
    "golang": "a scratch or distroless image that contains only the compiled binary",
    "rust": "a slim or distroless image that contains only the compiled binary",
    "maven": "a JRE image that contains only the built artifact",
    "gradle": "a JRE image that contains only the built artifact",
    "gcc": "a slim runtime image that contains only the compiled binary",
}


def _check_sdk_final_image(lines: list[str]) -> list[DockerfileIssue]:
    """Flag a compiler SDK that is still the image being shipped.

    A second FROM means a build stage already exists. The finding stays when
    that later stage is still the SDK, because the compilers ship anyway.
    """
    stage = _final_stage(lines)
    from_instruction = _first_from(stage)
    if from_instruction is None:
        return []
    number, raw = from_instruction
    image = _image_reference(raw).split("@", 1)[0]
    repository = image.split("/")[-1].split(":")[0].lower()
    runtime = _SDK_RUNTIMES.get(repository)
    if runtime is None:
        return []
    stage_count = sum(
        1 for item in _stages(lines) if item and item[0][1].upper().startswith("FROM ")
    )
    if stage_count >= 2:
        detail = (
            f"Line {number} uses `{image}` for the final stage, so the compiler toolchain "
            "is still part of the shipped image."
        )
        suggestion = f"Keep `{repository}` in the build stage and copy the artifact into {runtime}."
    else:
        detail = f"Line {number} uses `{image}` as the only stage, so the SDK ships with the application."
        suggestion = (
            f"Add a multi-stage build. Compile here, then copy the artifact into {runtime}."
        )
    return [
        DockerfileIssue(
            code="sdk-final-image",
            severity="medium",
            title="Final image includes a compiler SDK",
            detail=detail,
            suggestion=suggestion,
            line=number,
        )
    ]


_BUILD_PACKAGES = (
    "build-essential",
    "g++",
    "gcc",
    "make",
    "cmake",
    "pkg-config",
    "python3-dev",
    "python-dev",
    "musl-dev",
    "libc-dev",
    "linux-headers",
)
_PACKAGE_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9.+-]*")


def _check_build_dependencies(lines: list[str]) -> list[DockerfileIssue]:
    """Flag compilers installed in the stage that gets shipped.

    Packages removed in the same RUN, or by a later RUN in that stage, are
    not left in the image and are ignored. Earlier build stages are ignored.
    """
    lingering: list[int] = []
    for number, raw in _final_stage(lines):
        if not raw.upper().startswith("RUN "):
            continue
        if _installs_build_tool(raw) and not _removes_build_tool(raw):
            lingering.append(number)
        elif _removes_build_tool(raw):
            lingering.clear()
    if not lingering:
        return []
    line = lingering[0]
    return [
        DockerfileIssue(
            code="build-deps-in-final-image",
            severity="medium",
            title="Build tools remain in the final image",
            detail=(
                f"Line {line} installs a compiler or development headers in the stage that ships."
            ),
            suggestion=(
                "Install build tools in an earlier stage and copy only the artifact forward, "
                "or remove the packages in the same RUN instruction."
            ),
            line=line,
        )
    ]


def _installs_build_tool(instruction: str) -> bool:
    lowered = instruction.lower()
    if not re.search(r"\b(apt-get|apt|apk|yum|dnf|microdnf)\b", lowered):
        return False
    if not re.search(r"\b(install|add)\b", lowered):
        return False
    return _mentions_build_package(lowered)


def _removes_build_tool(instruction: str) -> bool:
    lowered = instruction.lower()
    if not re.search(r"\b(remove|purge|autoremove|del)\b", lowered):
        return False
    return _mentions_build_package(lowered)


def _mentions_build_package(text: str) -> bool:
    for token in _PACKAGE_TOKEN_RE.findall(text):
        for package in _BUILD_PACKAGES:
            if (
                token == package
                or token.startswith(f"{package}-")
                or token.startswith(f"{package}=")
            ):
                return True
    return False


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


_APT_UPDATE_RE = re.compile(r"\bapt(?:-get)?\s+update\b", re.IGNORECASE)
_APT_INSTALL_RE = re.compile(r"\bapt(?:-get)?\s+install\b", re.IGNORECASE)


def _check_split_apt(lines: list[str]) -> list[DockerfileIssue]:
    """Flag apt update and install when they are not in the same RUN.

    A separate update layer goes stale, and a later install can fail or
    reuse an old package index. One RUN keeps the index and the install together.
    """
    issues: list[DockerfileIssue] = []
    for number, raw in _instructions(lines):
        if not raw.upper().startswith("RUN "):
            continue
        has_update = _APT_UPDATE_RE.search(raw) is not None
        has_install = _APT_INSTALL_RE.search(raw) is not None
        if has_update == has_install:
            continue
        if has_update:
            detail = f"Line {number} runs apt-get update without installing packages in that RUN."
            suggestion = "Chain `apt-get update` and `apt-get install` in one RUN, then delete the package lists."
        else:
            detail = (
                f"Line {number} installs apt packages without `apt-get update` in the same RUN."
            )
            suggestion = "Run `apt-get update && apt-get install` in the same RUN so the index cannot go stale."
        issues.append(
            DockerfileIssue(
                code="split-apt-command",
                severity="medium",
                title="apt update and install are not in the same RUN",
                detail=detail,
                suggestion=suggestion,
                line=number,
            )
        )
    return issues


def _check_apt_recommends(lines: list[str]) -> list[DockerfileIssue]:
    """Flag apt installs that pull recommended packages."""
    issues: list[DockerfileIssue] = []
    for number, raw in _instructions(lines):
        if not raw.upper().startswith("RUN "):
            continue
        if _APT_INSTALL_RE.search(raw) is None or "--no-install-recommends" in raw.lower():
            continue
        issues.append(
            DockerfileIssue(
                code="apt-recommends",
                severity="low",
                title="apt install includes recommended packages",
                detail=(
                    f"Line {number} does not pass `--no-install-recommends`, "
                    "so apt may install extra packages the process never uses."
                ),
                suggestion=(
                    "Add `--no-install-recommends` unless one of those recommended packages is required."
                ),
                line=number,
            )
        )
    return issues


def _check_consecutive_runs(lines: list[str]) -> list[DockerfileIssue]:
    """Flag adjacent RUN instructions in the same stage.

    Each RUN is its own layer. A COPY or ADD between them is a real cache
    boundary, so those runs are left alone.
    """
    issues: list[DockerfileIssue] = []
    for stage in _stages(lines):
        group: list[int] = []
        for number, raw in stage:
            if raw.upper().startswith("RUN "):
                group.append(number)
                continue
            if len(group) >= 2:
                issues.append(_consecutive_run_issue(group))
            group = []
        if len(group) >= 2:
            issues.append(_consecutive_run_issue(group))
    return issues


def _consecutive_run_issue(lines: list[int]) -> DockerfileIssue:
    return DockerfileIssue(
        code="consecutive-run",
        severity="low",
        title="Consecutive RUN instructions add extra layers",
        detail=(
            f"Lines {lines[0]} and {lines[1]} are adjacent RUN instructions. "
            f"{len(lines)} layers can be one layer when they do not need separate cache points."
        ),
        suggestion=(
            "Combine those RUN instructions with && when a cache boundary is not useful. "
            "Leave them split when a later edit should reuse the earlier layer."
        ),
        line=lines[1],
    )


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


_COMMAND_RE = re.compile(r"^(CMD|ENTRYPOINT)\s+(.*)$", re.IGNORECASE)


def _check_exec_form(lines: list[str]) -> list[DockerfileIssue]:
    """Flag shell-form CMD or ENTRYPOINT.

    Shell form wraps the process in `/bin/sh -c`, so the shell is PID 1 and
    may ignore SIGTERM. Only the last instruction of each kind takes effect.
    """
    last: dict[str, tuple[int, str]] = {}
    for number, raw in _instructions(lines):
        match = _COMMAND_RE.match(raw)
        if match:
            last[match.group(1).upper()] = (number, match.group(2).strip())
    issues: list[DockerfileIssue] = []
    for kind, (number, args) in last.items():
        if args.startswith("["):
            continue
        issues.append(
            DockerfileIssue(
                code="shell-form-command",
                severity="medium",
                title=f"{kind} uses shell form",
                detail=(
                    f"Line {number} uses shell form, so a shell becomes PID 1 and can swallow SIGTERM."
                ),
                suggestion=(
                    "Use exec form so the process receives shutdown signals, "
                    f'for example `{kind} ["executable", "arg"]`.'
                ),
                line=number,
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


def _check_healthcheck(lines: list[str], ports: list[int]) -> list[DockerfileIssue]:
    for _number, raw in _instructions(lines):
        if raw.upper().startswith("HEALTHCHECK "):
            return []
    if ports:
        suggestion = (
            "Add a HEALTHCHECK that probes the application without a new package, "
            "for example `HEALTHCHECK CMD python -c "
            f"\"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{ports[0]}/health')\"`."
        )
    else:
        suggestion = "Add a HEALTHCHECK that probes a local readiness endpoint."
    return [
        DockerfileIssue(
            code="missing-healthcheck",
            severity="low",
            title="No HEALTHCHECK instruction",
            detail=(
                "Orchestrators cannot tell a running process from an application that is ready to serve."
            ),
            suggestion=suggestion,
        )
    ]


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


def _final_stage(lines: list[str]) -> list[tuple[int, str]]:
    stages = [
        stage for stage in _stages(lines) if stage and stage[0][1].upper().startswith("FROM ")
    ]
    return stages[-1] if stages else []


def _first_from(stage: list[tuple[int, str]]) -> tuple[int, str] | None:
    for instruction in stage:
        if instruction[1].upper().startswith("FROM "):
            return instruction
    return None


def _stages(lines: list[str]) -> list[list[tuple[int, str]]]:
    stages: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for instruction in _instructions(lines):
        if instruction[1].upper().startswith("FROM ") and current:
            stages.append(current)
            current = [instruction]
            continue
        current.append(instruction)
    if current:
        stages.append(current)
    return stages


def _image_reference(instruction: str) -> str:
    """Return the image token from a FROM instruction, ignoring flags and stage names."""
    tokens = instruction.split()
    if not tokens or tokens[0].upper() != "FROM":
        return ""
    index = 1
    while index < len(tokens) and tokens[index].startswith("--"):
        index += 2 if "=" not in tokens[index] else 1
    if index >= len(tokens):
        return ""
    return tokens[index]


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
