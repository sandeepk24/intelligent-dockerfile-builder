"""Optional Trivy image scanning."""

from __future__ import annotations

import json
import shutil

from app.core.config import settings
from app.validators.commands import run_command


def trivy_available() -> bool:
    return shutil.which(settings.trivy_bin) is not None or shutil.which("trivy") is not None


async def scan_image(image_tag: str) -> dict:
    if not settings.trivy_enabled and not trivy_available():
        return {
            "status": "skipped",
            "reason": "trivy is not installed",
            "findings": [],
        }
    binary = shutil.which(settings.trivy_bin) or shutil.which("trivy")
    if binary is None:
        return {
            "status": "skipped",
            "reason": "trivy is not installed",
            "findings": [],
        }

    result = await run_command(
        [
            binary,
            "image",
            "--quiet",
            "--format",
            "json",
            "--severity",
            "HIGH,CRITICAL",
            "--no-progress",
            image_tag,
        ],
        timeout=180,
    )
    findings = _parse_findings(result.stdout)
    status = "failed" if findings else "passed"
    if result.timed_out:
        status = "failed"
    return {
        "status": status,
        "reason": None,
        "findings": findings[:50],
        "finding_count": len(findings),
    }


def _parse_findings(stdout: str) -> list[dict]:
    if not stdout.strip():
        return []
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    results = payload.get("Results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []
    findings: list[dict] = []
    for result in results:
        vulns = result.get("Vulnerabilities") or []
        if not isinstance(vulns, list):
            continue
        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue
            findings.append(
                {
                    "id": vuln.get("VulnerabilityID"),
                    "severity": vuln.get("Severity"),
                    "pkg": vuln.get("PkgName"),
                    "title": vuln.get("Title") or vuln.get("VulnerabilityID"),
                }
            )
    return findings
