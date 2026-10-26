"""Generate a Dockerfile from analyzed project context via the LLM provider."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.analyzers.base import Analysis
from app.analyzers.dockerfile_review import DockerfileIssue
from app.generators.prompts import (
    OPTIMIZE_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_optimize_prompt,
    build_repair_prompt,
    build_user_prompt,
)
from app.llm.provider import LLMProvider
from app.models.records import ProjectRecord


class LLMIssue(BaseModel):
    code: str = "review"
    severity: str = "medium"
    title: str
    detail: str = ""
    suggestion: str = ""
    line: int | None = None


class LLMDockerfile(BaseModel):
    dockerfile: str = Field(min_length=8)
    explanation: str = ""
    decisions: list[str] = Field(default_factory=list)
    issues: list[LLMIssue] = Field(default_factory=list)
    root_cause: str = ""

    @field_validator("dockerfile")
    @classmethod
    def must_contain_from(cls, value: str) -> str:
        cleaned = _strip_fences(value)
        has_from = any(line.strip().upper().startswith("FROM") for line in cleaned.splitlines())
        if not has_from:
            raise ValueError("Model output did not include a FROM instruction")
        return cleaned


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:dockerfile)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip() + "\n"


def project_to_analysis(project: ProjectRecord) -> Analysis:
    return Analysis(
        language=project.language,
        framework=project.framework,
        entry_point=project.entry_point,
        runtime_version=project.runtime_version,
        dependencies=project.dependencies,
        ports=project.ports,
        build_command=project.build_command,
        start_command=project.start_command,
    )


async def generate_from_project(
    project: ProjectRecord,
    provider: LLMProvider,
    *,
    model: str,
    instructions: str | None = None,
) -> LLMDockerfile:
    prompt = build_user_prompt(
        language=project.language,
        framework=project.framework,
        entry_point=project.entry_point,
        runtime_version=project.runtime_version,
        dependencies=project.dependencies,
        ports=project.ports,
        build_command=project.build_command,
        start_command=project.start_command,
        file_tree=project.file_tree,
        key_files=project.key_files,
        instructions=instructions,
    )
    raw = await provider.generate_json(model=model, prompt=prompt, system=SYSTEM_PROMPT)
    return LLMDockerfile.model_validate(raw)


async def optimize_from_project(
    project: ProjectRecord,
    provider: LLMProvider,
    *,
    model: str,
    dockerfile: str,
    static_issues: list[DockerfileIssue],
    instructions: str | None = None,
) -> LLMDockerfile:
    prompt = build_optimize_prompt(
        language=project.language,
        framework=project.framework,
        entry_point=project.entry_point,
        runtime_version=project.runtime_version,
        dependencies=project.dependencies,
        ports=project.ports,
        start_command=project.start_command,
        file_tree=project.file_tree,
        key_files=project.key_files,
        dockerfile=dockerfile,
        static_issues=[issue.to_dict() for issue in static_issues],
        instructions=instructions,
    )
    raw = await provider.generate_json(model=model, prompt=prompt, system=OPTIMIZE_SYSTEM_PROMPT)
    return LLMDockerfile.model_validate(raw)


async def repair_from_failure(
    project: ProjectRecord,
    provider: LLMProvider,
    *,
    model: str,
    dockerfile: str,
    error_log: str,
    lint_findings: list[dict],
    instructions: str | None = None,
) -> LLMDockerfile:
    prompt = build_repair_prompt(
        language=project.language,
        framework=project.framework,
        entry_point=project.entry_point,
        start_command=project.start_command,
        dockerfile=dockerfile,
        error_log=error_log,
        lint_findings=lint_findings,
        instructions=instructions,
    )
    raw = await provider.generate_json(model=model, prompt=prompt, system=REPAIR_SYSTEM_PROMPT)
    return LLMDockerfile.model_validate(raw)
