"""Run Hadolint against a Dockerfile when the binary is available."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.config import settings
from app.validators.commands import run_command


async def run_hadolint(dockerfile: Path) -> dict:
    binary = shutil.which(settings.hadolint_bin) or shutil.which("hadolint")
    if binary is None:
        return {
            "status": "skipped",
            "reason": "hadolint is not installed",
            "findings": [],
        }

    result = await run_command(
        [binary, "-f", "json", str(dockerfile)],
        timeout=30,
        cwd=dockerfile.parent,
    )
    findings = _parse_findings(result.stdout)
    status = "failed" if result.returncode != 0 or _has_error(findings) else "passed"
    if result.timed_out:
        status = "failed"
    return {
        "status": status,
        "reason": None,
        "findings": findings,
        "returncode": result.returncode,
        "stderr": result.stderr[-2000:] if result.stderr else "",
    }


def _parse_findings(stdout: str) -> list[dict]:
    if not stdout.strip():
        return []
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return [
            {
                "code": "hadolint-output",
                "level": "info",
                "message": stdout[:1000],
                "line": None,
            }
        ]
    if not isinstance(payload, list):
        return []
    findings = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        findings.append(
            {
                "code": item.get("code") or "DL0000",
                "level": str(item.get("level") or "info").lower(),
                "message": item.get("message") or "",
                "line": item.get("line"),
            }
        )
    return findings


def _has_error(findings: list[dict]) -> bool:
    return any(item.get("level") in {"error", "fatal"} for item in findings)
