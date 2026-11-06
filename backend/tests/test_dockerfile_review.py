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


def test_flags_full_official_base_when_a_smaller_variant_exists():
    issues = review_dockerfile(_runtime_dockerfile("python:3.12"), ports=[8000])
    match = next(issue for issue in issues if issue.code == "full-base-image")
    assert match.severity == "medium"
    assert "python:3.12-slim" in match.suggestion

    bookworm = review_dockerfile(_runtime_dockerfile("python:3.12-bookworm"), ports=[8000])
    assert "full-base-image" in {issue.code for issue in bookworm}


def test_smaller_base_variants_are_not_flagged():
    for image in (
        "python:3.12-slim",
        "python:3.12-alpine",
        "node:22-alpine",
        "eclipse-temurin:21-jre",
    ):
        issues = review_dockerfile(_runtime_dockerfile(image), ports=[8000])
        assert "full-base-image" not in {issue.code for issue in issues}, image


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


def _runtime_dockerfile(image: str) -> str:
    return f"""\
FROM {image}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app"]
"""
