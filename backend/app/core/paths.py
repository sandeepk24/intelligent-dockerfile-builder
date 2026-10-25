"""Safe path resolution confined to the configured workspace root."""

from pathlib import Path

from app.core.config import settings


class WorkspacePathError(ValueError):
    """Raised when a requested path escapes the workspace root."""


def workspace_root() -> Path:
    root = Path(settings.workspace_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_workspace_path(relative_path: str) -> Path:
    """Resolve a user-supplied relative path inside WORKSPACE_ROOT."""
    if not relative_path or relative_path.strip() != relative_path:
        raise WorkspacePathError("Path must be a relative workspace location")

    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise WorkspacePathError("Path traversal is not allowed")

    root = workspace_root()
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise WorkspacePathError("Path is outside the configured workspace root")
    return resolved
