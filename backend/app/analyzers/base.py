"""Shared analysis result type."""

from dataclasses import dataclass, field


@dataclass
class Analysis:
    language: str | None = None
    framework: str | None = None
    entry_point: str | None = None
    runtime_version: str | None = None
    dependencies: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    build_command: str | None = None
    start_command: str | None = None
