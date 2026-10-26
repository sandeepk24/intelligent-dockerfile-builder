"""Isolated Docker image builds for untrusted projects."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.validators.commands import run_command
from app.validators.sanitize import sanitize_log

logger = get_logger(__name__)


def docker_available() -> bool:
    return shutil.which("docker") is not None


async def build_image(context: Path, image_tag: str) -> dict:
    """Build an image without privileged mode. Network is required to pull bases."""
    if not docker_available():
        return {
            "status": "skipped",
            "reason": "docker CLI is not installed",
            "image_tag": None,
            "log": None,
        }
    if not settings.docker_allow_builds:
        return {
            "status": "skipped",
            "reason": "Docker builds are disabled by configuration",
            "image_tag": None,
            "log": None,
        }

    started = time.perf_counter()
    args = [
        "docker",
        "build",
        "--pull=false",
        "--network=default",
        f"--tag={image_tag}",
        "--label=com.intelligentdockerfile.builder=1",
        ".",
    ]
    result = await run_command(args, timeout=settings.docker_build_timeout, cwd=context)
    duration_ms = int((time.perf_counter() - started) * 1000)
    combined = sanitize_log(
        "\n".join(part for part in (result.stdout, result.stderr) if part),
        extra_paths=[str(context)],
    )
    if result.timed_out:
        return {
            "status": "failed",
            "reason": f"docker build timed out after {settings.docker_build_timeout}s",
            "image_tag": None,
            "log": combined,
            "duration_ms": duration_ms,
        }
    if result.returncode != 0:
        return {
            "status": "failed",
            "reason": "docker build exited with a non-zero status",
            "image_tag": None,
            "log": combined,
            "duration_ms": duration_ms,
        }
    size = await inspect_image_size(image_tag)
    return {
        "status": "passed",
        "reason": None,
        "image_tag": image_tag,
        "log": combined,
        "duration_ms": duration_ms,
        "image_size_bytes": size,
    }


async def inspect_image_size(image_tag: str) -> int | None:
    result = await run_command(
        ["docker", "image", "inspect", "--format", "{{.Size}}", image_tag],
        timeout=15,
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


async def remove_image(image_tag: str) -> None:
    if not docker_available():
        return
    await run_command(["docker", "image", "rm", "-f", image_tag], timeout=30)
