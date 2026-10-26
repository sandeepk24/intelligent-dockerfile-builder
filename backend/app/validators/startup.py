"""Restricted process-start check for a built image.

Does not publish ports or attach the Docker socket. The container runs with
dropped capabilities, no new privileges, a PID limit, and no network.
"""

from __future__ import annotations

import asyncio

from app.core.config import settings
from app.validators.commands import run_command
from app.validators.sanitize import sanitize_log


async def check_startup(image_tag: str, *, name: str) -> dict:
    args = [
        "docker",
        "run",
        "--detach",
        "--name",
        name,
        "--network=none",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        f"--memory={settings.docker_build_memory_limit}",
        f"--cpus={settings.docker_build_cpu_limit}",
        "--pids-limit=128",
        "--read-only",
        "--tmpfs",
        "/tmp",
        image_tag,
    ]
    started = await run_command(args, timeout=30)
    if started.returncode != 0:
        return {
            "status": "failed",
            "reason": "container failed to start",
            "log": sanitize_log(started.stderr or started.stdout),
        }

    await asyncio.sleep(settings.startup_check_seconds)
    inspect = await run_command(
        ["docker", "inspect", "--format", "{{.State.Running}} {{.State.Status}}", name],
        timeout=10,
    )
    logs = await run_command(["docker", "logs", "--tail", "80", name], timeout=10)
    await run_command(["docker", "rm", "-f", name], timeout=15)

    running = inspect.stdout.strip().startswith("true")
    log = sanitize_log("\n".join(part for part in (logs.stdout, logs.stderr) if part))
    if running:
        return {
            "status": "passed",
            "reason": f"process stayed running for {settings.startup_check_seconds}s",
            "log": log,
        }
    return {
        "status": "failed",
        "reason": "process exited before the startup window elapsed",
        "log": log or sanitize_log(inspect.stderr),
    }
