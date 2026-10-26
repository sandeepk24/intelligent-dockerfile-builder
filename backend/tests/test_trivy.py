"""Tests for Trivy JSON parsing."""

from app.validators.trivy import _parse_findings


def test_parses_trivy_results():
    raw = """{
      "Results": [
        {
          "Vulnerabilities": [
            {
              "VulnerabilityID": "CVE-2024-1",
              "Severity": "HIGH",
              "PkgName": "openssl",
              "Title": "buffer overflow"
            }
          ]
        }
      ]
    }"""
    findings = _parse_findings(raw)
    assert findings[0]["id"] == "CVE-2024-1"
    assert findings[0]["pkg"] == "openssl"


def test_empty_trivy_output():
    assert _parse_findings("") == []
    assert _parse_findings("not-json") == []
