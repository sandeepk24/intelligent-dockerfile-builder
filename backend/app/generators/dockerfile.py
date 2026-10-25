"""Generate a Dockerfile from analyzed project context via the LLM provider."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.analyzers.base import Analysis
from app.generators.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.provider import LLMProvider
from app.models.records import ProjectRecord


class LLMDockerfile(BaseModel):
    dockerfile: str = Field(min_length=8)
    explanation: str = ""
    decisions: list[str] = Field(default_factory=list)

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
