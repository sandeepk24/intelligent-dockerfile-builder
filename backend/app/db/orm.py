"""SQLAlchemy ORM tables for persisted builder state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.records import utcnow


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    root_path: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    ports: Mapped[list] = mapped_column(JSON, default=list)
    build_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_dockerfile: Mapped[bool] = mapped_column(Boolean, default=False)
    existing_dockerfile: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_tree: Mapped[list] = mapped_column(JSON, default=list)
    key_files: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DockerfileRow(Base):
    __tablename__ = "dockerfiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    dockerfile: Mapped[str] = mapped_column(Text)
    dockerignore: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    decisions: Mapped[list] = mapped_column(JSON, default=list)
    model: Mapped[str] = mapped_column(String(128), index=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="generated", index=True)
    original_dockerfile: Mapped[str | None] = mapped_column(Text, nullable=True)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    repair_attempt: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    dockerfile_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    validation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ValidationRow(Base):
    __tablename__ = "validations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dockerfile_id: Mapped[str] = mapped_column(ForeignKey("dockerfiles.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    lint: Mapped[dict] = mapped_column(JSON, default=dict)
    build: Mapped[dict] = mapped_column(JSON, default=dict)
    image_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    build_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trivy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    startup: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_build: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RepairRow(Base):
    __tablename__ = "repairs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    validation_id: Mapped[str] = mapped_column(ForeignKey("validations.id"), index=True)
    source_dockerfile_id: Mapped[str] = mapped_column(String(36), index=True)
    result_dockerfile_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    root_cause: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    decisions: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationRow(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    dockerfile_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    validation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    image_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    build_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lint_finding_count: Mapped[int] = mapped_column(Integer, default=0)
    trivy_finding_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SettingRow(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
