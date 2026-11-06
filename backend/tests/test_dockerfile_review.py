"""Tests for deterministic Dockerfile issue detection."""

from pathlib import Path

from app.analyzers.dockerfile_review import review_dockerfile

SAMPLE = (
    Path(__file__).resolve().parents[2] / "sample-projects" / "python-unoptimized" / "Dockerfile"
)


def test_flags_shell_form_startup_commands():
    dockerfile = """\
FROM python:3.12-slim
WORKDIR /app
USER appuser
EXPOSE 8000
ENTRYPOINT python -m app
CMD python -m app
"""
    issues = [
        issue for issue in review_dockerfile(dockerfile) if issue.code == "shell-form-command"
    ]
    assert {issue.title for issue in issues} == {
        "ENTRYPOINT uses shell form",
        "CMD uses shell form",
    }
    assert all(issue.severity == "medium" for issue in issues)


def test_exec_form_and_overridden_shell_form_are_not_flagged():
    dockerfile = """\
FROM python:3.12-slim
CMD python -m app
ENTRYPOINT ["python", "-m", "app"]
CMD ["python", "-m", "app"]
USER appuser
"""
    issues = review_dockerfile(dockerfile)
    assert "shell-form-command" not in {issue.code for issue in issues}


def test_flags_common_problems_in_unoptimized_sample():
    issues = review_dockerfile(SAMPLE.read_text(), ports=[8000])
    codes = {issue.code for issue in issues}
    assert "latest-tag" in codes
    assert "add-instead-of-copy" in codes
    assert "pip-cache" in codes
    assert "copies-secrets" in codes
    assert "explicit-root-user" in codes
    assert "copy-context-too-early" in codes
    assert "shell-form-command" in codes


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


def test_flags_build_tools_left_in_the_final_stage():
    dockerfile = """\
FROM python:3.12-slim
RUN apt-get update && apt-get install -y build-essential \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
"""
    issues = review_dockerfile(dockerfile)
    assert any(issue.code == "build-deps-in-final-image" for issue in issues)

    alpine = """\
FROM python:3.12-alpine
RUN apk add --no-cache g++ musl-dev
CMD ["python", "app.py"]
"""
    issues = review_dockerfile(alpine)
    assert any(issue.code == "build-deps-in-final-image" for issue in issues)


def test_build_tools_removed_or_isolated_are_not_flagged():
    purged = """\
FROM python:3.12-slim
RUN apt-get update && apt-get install -y gcc \\
    && apt-get purge -y gcc \\
    && rm -rf /var/lib/apt/lists/*
CMD ["python", "app.py"]
"""
    isolated = """\
FROM python:3.12-slim AS build
RUN apt-get update && apt-get install -y build-essential
FROM python:3.12-slim
COPY --from=build /app /app
USER appuser
CMD ["python", "-m", "app"]
"""
    for dockerfile in (purged, isolated):
        issues = review_dockerfile(dockerfile)
        assert "build-deps-in-final-image" not in {issue.code for issue in issues}


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
