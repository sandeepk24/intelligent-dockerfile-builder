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


def test_flags_sdk_image_used_as_the_shipped_image():
    single_stage = """\
FROM golang:1.23-alpine
WORKDIR /src
COPY . .
RUN go build -o /out/app .
CMD ["/out/app"]
"""
    issues = review_dockerfile(single_stage)
    match = next(issue for issue in issues if issue.code == "sdk-final-image")
    assert "multi-stage" in match.suggestion

    final_stage_still_sdk = """\
FROM golang:1.23-alpine AS build
WORKDIR /src
RUN go build -o /out/app .
FROM golang:1.23-alpine
COPY --from=build /out/app /out/app
CMD ["/out/app"]
"""
    issues = review_dockerfile(final_stage_still_sdk)
    assert any(issue.code == "sdk-final-image" for issue in issues)


def test_runtime_stage_after_sdk_is_not_flagged():
    dockerfile = """\
FROM golang:1.23-alpine AS build
WORKDIR /src
RUN go build -o /out/app .
FROM gcr.io/distroless/static-debian12
COPY --from=build /out/app /out/app
USER nonroot
CMD ["/out/app"]
"""
    issues = review_dockerfile(dockerfile)
    assert "sdk-final-image" not in {issue.code for issue in issues}


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
