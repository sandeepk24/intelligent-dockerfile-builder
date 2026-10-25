"""Tests for deterministic Dockerfile issue detection."""

from pathlib import Path

from app.analyzers.dockerfile_review import review_dockerfile

SAMPLE = (
    Path(__file__).resolve().parents[2] / "sample-projects" / "python-unoptimized" / "Dockerfile"
)


def test_flags_common_problems_in_unoptimized_sample():
    issues = review_dockerfile(SAMPLE.read_text(), ports=[8000])
    codes = {issue.code for issue in issues}
    assert "latest-tag" in codes
    assert "add-instead-of-copy" in codes
    assert "pip-cache" in codes
    assert "copies-secrets" in codes
    assert "explicit-root-user" in codes
    assert "copy-context-too-early" in codes


def test_clean_dockerfile_has_no_high_severity_issues():
    dockerfile = """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    issues = review_dockerfile(dockerfile, ports=[8000])
    assert [issue.code for issue in issues if issue.severity == "high"] == []
