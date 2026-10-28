"""SQLite persistence survives a new store instance on the same file."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import inspect

from app.db.engine import make_engine
from app.db.sqlite_store import SqliteStore
from app.db.store import persist_settings, store
from app.models.records import DockerfileRecord, ProjectRecord


def test_sqlite_round_trip_survives_reopen(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'builder.db'}"
    first = SqliteStore(url)
    first.save_project(
        ProjectRecord(
            id="p1",
            source_type="directory",
            name="demo",
            root_path="/tmp/demo",
            language="python",
            framework="fastapi",
        )
    )
    first.save_dockerfile(
        DockerfileRecord(
            id="df-1",
            project_id="p1",
            dockerfile="FROM python:3.12-slim\n",
            dockerignore=".venv\n",
            explanation="slim",
            decisions=["pin tag"],
            model="codellama:7b",
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    )
    first.set_setting("ollama_default_model", "llama3.2:3b")

    second = SqliteStore(url)
    loaded = second.get_dockerfile("df-1")
    assert loaded is not None
    assert "python:3.12-slim" in loaded.dockerfile
    history = second.list_dockerfiles(language="python", query="demo")
    assert [item.id for item in history] == ["df-1"]
    assert second.get_setting("ollama_default_model") == "llama3.2:3b"


def test_sqlite_settings_round_trip_via_proxy(tmp_path: Path):
    from app.core.config import settings

    url = f"sqlite:///{tmp_path / 'settings.db'}"
    store.configure(SqliteStore(url), "sqlite")
    original = settings.ollama_default_model
    settings.ollama_default_model = "phi3:mini"
    persist_settings()
    reopened = SqliteStore(url)
    assert reopened.get_setting("ollama_default_model") == "phi3:mini"
    settings.ollama_default_model = original


def test_alembic_upgrade_creates_expected_tables(tmp_path: Path):
    from alembic.config import Config

    from alembic import command
    from app.core.config import settings

    db = tmp_path / "alembic.db"
    original = settings.database_url
    settings.database_url = f"sqlite:///{db}"
    try:
        ini = Path(__file__).resolve().parents[1] / "alembic.ini"
        cfg = Config(str(ini))
        cfg.set_main_option("script_location", str(ini.parent / "alembic"))
        command.upgrade(cfg, "head")
        tables = set(inspect(make_engine(f"sqlite:///{db}")).get_table_names())
        assert {
            "projects",
            "dockerfiles",
            "validations",
            "repairs",
            "evaluations",
            "app_settings",
        } <= tables
    finally:
        settings.database_url = original
