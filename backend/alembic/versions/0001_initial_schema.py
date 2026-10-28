"""Initial SQLite schema for projects, Dockerfiles, validations, and metrics.

Revision ID: 0001
Revises:
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("root_path", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("framework", sa.String(length=64), nullable=True),
        sa.Column("entry_point", sa.String(length=255), nullable=True),
        sa.Column("runtime_version", sa.String(length=64), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column("ports", sa.JSON(), nullable=False),
        sa.Column("build_command", sa.Text(), nullable=True),
        sa.Column("start_command", sa.Text(), nullable=True),
        sa.Column("has_dockerfile", sa.Boolean(), nullable=False),
        sa.Column("existing_dockerfile", sa.Text(), nullable=True),
        sa.Column("file_tree", sa.JSON(), nullable=False),
        sa.Column("key_files", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dockerfiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("dockerfile", sa.Text(), nullable=False),
        sa.Column("dockerignore", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("decisions", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("original_dockerfile", sa.Text(), nullable=True),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("repair_attempt", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dockerfiles_project_id", "dockerfiles", ["project_id"])
    op.create_index("ix_dockerfiles_model", "dockerfiles", ["model"])
    op.create_index("ix_dockerfiles_status", "dockerfiles", ["status"])
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dockerfile_id", sa.String(length=36), nullable=True),
        sa.Column("validation_id", sa.String(length=36), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "validations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "dockerfile_id", sa.String(length=36), sa.ForeignKey("dockerfiles.id"), nullable=False
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("lint", sa.JSON(), nullable=False),
        sa.Column("build", sa.JSON(), nullable=False),
        sa.Column("image_size_bytes", sa.Integer(), nullable=True),
        sa.Column("build_duration_ms", sa.Integer(), nullable=True),
        sa.Column("trivy", sa.JSON(), nullable=True),
        sa.Column("startup", sa.JSON(), nullable=True),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("approved_build", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_validations_dockerfile_id", "validations", ["dockerfile_id"])
    op.create_index("ix_validations_status", "validations", ["status"])
    op.create_table(
        "repairs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "validation_id", sa.String(length=36), sa.ForeignKey("validations.id"), nullable=False
        ),
        sa.Column("source_dockerfile_id", sa.String(length=36), nullable=False),
        sa.Column("result_dockerfile_id", sa.String(length=36), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("decisions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repairs_validation_id", "repairs", ["validation_id"])
    op.create_index("ix_repairs_source_dockerfile_id", "repairs", ["source_dockerfile_id"])
    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dockerfile_id", sa.String(length=36), nullable=True),
        sa.Column("validation_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("framework", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("image_size_bytes", sa.Integer(), nullable=True),
        sa.Column("build_duration_ms", sa.Integer(), nullable=True),
        sa.Column("lint_finding_count", sa.Integer(), nullable=False),
        sa.Column("trivy_finding_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluations_event", "evaluations", ["event"])
    op.create_index("ix_evaluations_status", "evaluations", ["status"])
    op.create_index("ix_evaluations_dockerfile_id", "evaluations", ["dockerfile_id"])
    op.create_index("ix_evaluations_language", "evaluations", ["language"])
    op.create_index("ix_evaluations_model", "evaluations", ["model"])
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("evaluations")
    op.drop_table("repairs")
    op.drop_table("validations")
    op.drop_table("jobs")
    op.drop_table("dockerfiles")
    op.drop_table("projects")
