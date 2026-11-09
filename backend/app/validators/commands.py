"""Async subprocess helper for validator tools."""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


async def run_command(
    args: list[str],
    *,
    timeout: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a subprocess with a hard timeout. Never uses a shell.

    The child is started in its own session so a timeout can signal the
    whole process group. Killing only the direct child would leave
    grandchildren running.
    """
    kwargs: dict = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
    }
    if os.name != "nt":
        kwargs["start_new_session"] = True
    process = await asyncio.create_subprocess_exec(*args, **kwargs)
    try:
        stdout_b, stderr_b = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        await _kill_process_group(process)
        return CommandResult(
            args=args,
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout}s: {' '.join(args)}",
            timed_out=True,
        )
    return CommandResult(
        args=args,
        returncode=process.returncode or 0,
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
    )


async def _kill_process_group(process: asyncio.subprocess.Process) -> None:
    """SIGKILL the child's process group, then reap it and drain its pipes."""
    pid = process.pid
    if process.returncode is None and pid:
        try:
            if os.name != "nt":
                os.killpg(pid, signal.SIGKILL)
            else:
                process.kill()
        except ProcessLookupError:
            pass
        except PermissionError:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        await process.wait()
