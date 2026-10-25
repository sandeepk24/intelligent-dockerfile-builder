"""Paths and files that must never be scanned or sent to the LLM."""

from pathlib import Path

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".eggs",
    ".venv",
    "venv",
    "env",
    "virtualenv",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    "target",
    "vendor",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".ds_store",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials.json",
    "credentials.yaml",
    "secrets.yaml",
    "secrets.yml",
    "serviceaccount.json",
}

EXCLUDED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".der",
    ".jks",
    ".kdbx",
}

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".mod",
    ".sum",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".txt",
    ".md",
    ".cfg",
    ".ini",
    ".gradle",
    ".xml",
    ".html",
    ".css",
    ".sh",
    ".dockerfile",
}

KEY_FILE_NAMES = {
    "dockerfile",
    ".dockerignore",
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "setup.py",
    "setup.cfg",
    "manage.py",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "makefile",
    ".python-version",
    "runtime.txt",
    "procfile",
    "app.py",
    "main.py",
    "main.go",
    "wsgi.py",
    "asgi.py",
}


def is_excluded_dir(name: str) -> bool:
    return name.lower() in EXCLUDED_DIR_NAMES


def is_excluded_file(path: Path) -> bool:
    name = path.name.lower()
    if name in EXCLUDED_FILE_NAMES or name.startswith(".env"):
        return True
    return path.suffix.lower() in EXCLUDED_SUFFIXES


def is_text_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        path.suffix.lower() in TEXT_SUFFIXES
        or name in KEY_FILE_NAMES
        or name
        in {
            "dockerfile",
            "makefile",
            "procfile",
            "pipfile",
        }
    )


def is_key_file(path: Path) -> bool:
    name = path.name.lower()
    if name in KEY_FILE_NAMES or name == "dockerfile":
        return True
    return path.suffix.lower() in {".py", ".go", ".js", ".ts"} and path.stem.lower() in {
        "main",
        "app",
        "index",
        "server",
        "wsgi",
        "asgi",
        "manage",
    }
