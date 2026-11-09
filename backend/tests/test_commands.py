"""Timeouts must reap the child and any process it spawned."""

from __future__ import annotations

import os
import sys
import textwrap

import pytest

from app.validators.commands import run_command


@pytest.mark.asyncio
async def test_command_returns_output_before_timeout():
    result = await run_command([sys.executable, "-c", "print('ok')"], timeout=10)
    assert result.timed_out is False
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-only")
@pytest.mark.asyncio
async def test_timeout_kills_the_process_group(tmp_path):
    pidfile = tmp_path / "child.pid"
    script = textwrap.dedent(
        """
        import os, sys, time
        path = sys.argv[1]
        pid = os.fork()
        if pid == 0:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            time.sleep(60)
        else:
            time.sleep(60)
        """
    )
    result = await run_command([sys.executable, "-c", script, str(pidfile)], timeout=2)
    assert result.timed_out is True
    assert result.returncode == -1
    child = int(pidfile.read_text(encoding="utf-8"))
    with pytest.raises(ProcessLookupError):
        os.kill(child, 0)
