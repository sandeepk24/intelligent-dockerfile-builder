# Intelligent Dockerfile Builder

An intelligent Dockerfile builder that analyzes application source code, generates optimized Dockerfiles using a locally hosted LLM (Ollama), validates Docker builds, and repairs build failures.

## Architecture

```
React + Vite SPA  →  REST API  →  FastAPI Backend  →  Ollama LLM
                                        ↓
                                 Project Analyzer
                                        ↓
                                Dockerfile Generator
                                        ↓
                                Validation Engine
                                   ↙        ↘
                               Success    AI Repair Loop (max 3)
                                   ↘        ↙
                                Evaluation Engine
                                        ↓
                                  SQLite Storage
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS, shadcn/ui, Monaco Editor |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| AI | Ollama (local), configurable open-weight models |
| Validation | Hadolint, Docker Engine, Trivy (optional) |
| Database | SQLite with Alembic migrations |

## Prerequisites

- **Node.js** 20+
- **Python** 3.12+
- **Ollama** — [Install Ollama](https://ollama.ai/download)
- **Docker** — for build validation (optional for generation)
- **Hadolint** — for Dockerfile linting (optional)

## Ollama Setup

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server
ollama serve

# Pull a coding model
ollama pull codellama:7b
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

The backend defaults `WORKSPACE_ROOT` to `sample-projects/` in this repository, so the New Dockerfile page can analyze the FastAPI, Express, and Go samples without extra setup.

Generation requires a running Ollama server. Project analysis, ZIP upload, and history work without it. History is in-memory until Milestone 4.

## API Documentation

Once the backend is running, visit **http://localhost:8000/docs** for the interactive OpenAPI documentation.

## Project Structure

```
intelligent-dockerfile-builder/
├── frontend/          # React + Vite SPA
├── backend/           # FastAPI backend
├── prompts/           # LLM prompt templates
├── sample-projects/   # Test projects for validation
├── docs/              # Architecture documentation
├── .env.example       # Environment template
└── README.md
```

## Development

```bash
# Backend tests
cd backend && pytest

# Backend linting
cd backend && ruff check . && ruff format --check .

# Frontend type checking
cd frontend && npm run type-check

# Frontend linting
cd frontend && npm run lint
```

## License

MIT
