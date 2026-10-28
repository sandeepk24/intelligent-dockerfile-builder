"""Process-wide store proxy. Tests keep MemoryStore; the app uses SQLite."""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.db.engine import uses_sqlite
from app.db.memory_store import MemoryStore

logger = get_logger(__name__)


class StoreProxy:
    """Delegates to a memory or SQLite backend without rewriting services."""

    def __init__(self) -> None:
        self._backend: object = MemoryStore()
        self.configured = False
        self.kind = "memory"

    def configure(self, backend: object, kind: str) -> None:
        self._backend = backend
        self.kind = kind
        self.configured = True

    def __getattr__(self, name: str):
        return getattr(self._backend, name)


store = StoreProxy()


def configure_persistence() -> None:
    """Swap in SQLite when a database URL is configured."""
    if store.configured:
        return
    url = settings.database_url
    if uses_sqlite(url):
        from app.db.sqlite_store import SqliteStore

        store.configure(SqliteStore(url), "sqlite")
        logger.info("Using SQLite persistence")
        load_persisted_settings()
        return
    store.configure(MemoryStore(), "memory")
    logger.info("Using in-memory store")


PERSISTED_SETTING_KEYS = (
    "ollama_base_url",
    "ollama_default_model",
    "ollama_timeout",
    "max_repair_attempts",
)


def load_persisted_settings() -> None:
    from app.llm.ollama_client import ollama_client

    values = store.list_settings()
    for key in PERSISTED_SETTING_KEYS:
        if key not in values:
            continue
        raw = values[key]
        if key in {"ollama_timeout", "max_repair_attempts"}:
            setattr(settings, key, int(raw))
        else:
            setattr(settings, key, raw)
    ollama_client.base_url = settings.ollama_base_url
    ollama_client.timeout = settings.ollama_timeout


def persist_settings() -> None:
    store.set_setting("ollama_base_url", settings.ollama_base_url)
    store.set_setting("ollama_default_model", settings.ollama_default_model)
    store.set_setting("ollama_timeout", str(settings.ollama_timeout))
    store.set_setting("max_repair_attempts", str(settings.max_repair_attempts))
