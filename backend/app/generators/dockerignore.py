"""Deterministic .dockerignore generation from detected language."""

from app.analyzers.base import Analysis

_COMMON = """\
.git
.gitignore
.gitattributes
.github
.idea
.vscode
.DS_Store
*.md
.env
.env.*
*.pem
*.key
credentials.json
secrets.yaml
"""

_PYTHON = """\
__pycache__
*.py[cod]
.pytest_cache
.mypy_cache
.ruff_cache
.venv
venv
env
.coverage
htmlcov
dist
build
*.egg-info
"""

_NODE = """\
node_modules
npm-debug.log
yarn-error.log
coverage
.nyc_output
dist
build
.next
"""

_GO = """\
vendor
bin
*.exe
*.test
*.out
"""


def generate_dockerignore(analysis: Analysis) -> str:
    sections = [_COMMON.strip()]
    if analysis.language == "python":
        sections.append(_PYTHON.strip())
    elif analysis.language == "javascript":
        sections.append(_NODE.strip())
    elif analysis.language == "go":
        sections.append(_GO.strip())
    return "\n".join(sections) + "\n"
