# Intelligent Dockerfile Builder

A local, AI-assisted tool for turning an application into a production-oriented Dockerfile.

You point it at a project. It inspects the source, detects the language and how the app starts, then asks a local LLM (Ollama) to write a Dockerfile and `.dockerignore`. You review the result in a Monaco editor, edit it, download it, or regenerate it with extra instructions.

No paid LLM APIs. Nothing leaves your machine except the local Ollama call.

**Status:** Milestones 1 and 2 are working (analyze + generate). Docker build validation, Hadolint, Trivy, and AI repair are next.

---

## What it can do today

### 1. Analyze a real project

Open **New Dockerfile** and either:

- pick a directory from the configured workspace, or
- upload a project ZIP

The analyzer looks at manifests and entry files (not a full AST) and reports:

| Detection | Examples |
|-----------|----------|
| Language | Python, JavaScript/Node, Go |
| Framework | FastAPI, Flask, Django, Express, Nest, Fastify, Koa, Next, or generic Go |
| Entry point | `app/main.py`, `src/index.js`, `main.go`, `manage.py`, … |
| Runtime | Python 3.x, Node engines, Go version from `go.mod` |
| Dependencies | `requirements.txt` / `pyproject.toml`, `package.json`, `go.mod` |
| Ports | Values found in listen/port code, otherwise framework defaults (8000 / 3000 / 8080) |
| Start command | `uvicorn …`, `node src/index.js`, compiled Go binary, Flask/Django equivalents |
| Existing Dockerfile | Flagged if one is already in the tree |

Sample apps are included so you can try this immediately:

- `sample-projects/python-fastapi`
- `sample-projects/node-express`
- `sample-projects/go-api`

### 2. Generate a Dockerfile with a local model

After analysis, choose an Ollama model and optionally add instructions such as “prefer distroless” or “expose 8080”.

Generation runs as a **background job**. The API returns a job ID; the UI polls until the Dockerfile is ready. The HTTP request is not blocked on the model.

The model is asked to produce:

- a production-oriented **Dockerfile**
- a short **explanation** of the approach
- a list of **decisions** (base image, non-root user, layer caching, …)

A language-specific **`.dockerignore`** is generated deterministically (not left to the model), so `.env`, VCS, `node_modules`, `.venv`, and similar paths stay out of the build context.

Prompts wrap repository files as **untrusted data**. Source in the project cannot instruct the model to ignore the generation rules.

Typical Dockerfile goals the prompt enforces:

- minimal official base images with version tags
- multi-stage builds when they shrink the image
- non-root process user
- dependency install before copying application source (better layer cache)
- no secrets, `.env` files, or credentials baked in
- only detected ports exposed
- a correct startup command for the detected framework

### 3. Review, edit, and take the files away

The **Workspace** page opens a Monaco editor with syntax highlighting.

You can:

- switch between `Dockerfile`, `.dockerignore`, and the AI explanation
- edit the generated files
- save edits back to history
- copy the Dockerfile
- download both `Dockerfile` and `.dockerignore`
- regenerate with extra instructions (keeps the same analyzed project)

**History** lists every generation in the current backend process. **Dashboard** shows how many Dockerfiles were generated this session and the latest activity. **Settings** lets you change the Ollama URL, default model, timeout, and max repair attempts.

### 4. Stay inside a safe local boundary

The builder treats uploaded projects as untrusted:

- directory browsing is limited to `WORKSPACE_ROOT` (no `..`, no absolute paths)
- `.env`, keys, credentials, `.git`, `node_modules`, virtualenvs, and similar paths are skipped and never sent to the model
- ZIP uploads are checked for path traversal, symlinks, file-count limits, upload size, and zip bombs
- CORS is limited to the configured frontend origin
- there is no endpoint that runs arbitrary host commands from model output

---

## What it does not do yet

These are planned, not implemented:

| Feature | When |
|---------|------|
| Hadolint syntax/lint checks | Milestone 3 |
| Isolated Docker **build** validation with explicit approval | Milestone 3 |
| Image size inspection | Milestone 3 |
| Optional Trivy vulnerability scan | Milestone 3 |
| AI repair loop (max 3 attempts) when a build fails | Milestone 3 |
| SQLite history that survives a restart | Milestone 4 |
| Persistent evaluation metrics (build time, size, lint findings) | Milestone 4 |

Until then, history lives in memory. Restarting the backend clears generated Dockerfiles.

---

## How a generation works

```text
You choose a project or ZIP
            │
            ▼
   Project Analyzer
   language, framework, entry point,
   deps, ports, start command
            │
            ▼
   Context Builder
   sanitized file tree + key files
   (secrets and vendor dirs stripped)
            │
            ▼
   Local Ollama model
   JSON: Dockerfile + explanation + decisions
            │
            ▼
   .dockerignore from language templates
            │
            ▼
   Workspace editor
   review, edit, copy, download, regenerate
```

Ollama is behind an LLM **provider interface**. Application code does not call Ollama types directly, so a later Bedrock or OpenAI-compatible provider can replace it without changing analyzers or the UI.

---

## Using the app

### Prerequisites

- Node.js 20+
- Python 3.12+
- [Ollama](https://ollama.ai/download) for generation (analysis works without it)

Docker, Hadolint, and Trivy are not required until Milestone 3.

### Start Ollama

```bash
# macOS
brew install ollama

ollama serve
ollama pull codellama:7b
```

Any local coding model Ollama exposes will appear in the UI. Set `OLLAMA_DEFAULT_MODEL` if you prefer another tag.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/api/v1/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The Vite dev server proxies `/api` to the backend, so you do not need to hardcode a backend URL in the UI.

### First run

1. Confirm the sidebar shows **Backend** connected. **Ollama** should be green if `ollama serve` is running.
2. Go to **New Dockerfile**.
3. Choose `python-fastapi` (or upload a ZIP of your app).
4. Click **Analyze project** and check language, framework, entry point, and ports.
5. Pick a model and click **Generate Dockerfile**.
6. When the job finishes, the Workspace opens with the Dockerfile, ignore file, and explanation.

By default `WORKSPACE_ROOT` is this repo’s `sample-projects/` directory.

---

## Configuration

Copy `.env.example` to `.env` next to the backend. Important settings:

| Variable | Purpose |
|----------|---------|
| `OLLAMA_BASE_URL` | Local Ollama server (`http://localhost:11434`) |
| `OLLAMA_DEFAULT_MODEL` | Model used when the UI does not pick one |
| `WORKSPACE_ROOT` | Only directory the backend will browse |
| `MAX_UPLOAD_SIZE_MB` | ZIP upload cap (default 50) |
| `MAX_FILE_COUNT` | Max files in a scanned project or ZIP |
| `CORS_ORIGINS` | Allowed frontend origins |
| `VITE_API_BASE_URL` | Frontend API base; leave empty in dev to use the Vite proxy |

Ollama URL and default model can also be changed at runtime on the **Settings** page.

---

## Project layout

```
intelligent-dockerfile-builder/
├── frontend/              React 19 + Vite SPA (dashboard, generate, workspace)
├── backend/               FastAPI app, analyzers, LLM client, generators
├── prompts/               Dockerfile generation prompt notes
├── sample-projects/       FastAPI, Express, and Go apps for demos
├── docs/
│   ├── ARCHITECTURE.md    Component boundaries and security rules
│   ├── API.md             REST contracts
│   └── IMPLEMENTATION_PLAN.md
├── .env.example
└── README.md
```

---

## Development

```bash
# Backend
cd backend && pytest
cd backend && ruff check . && ruff format --check .

# Frontend
cd frontend && npm run type-check
cd frontend && npm run lint
cd frontend && npm run build
```

Analyzer and ZIP tests use the sample projects and do not need Ollama. Generation tests use a fake LLM so CI does not call a live model.

## License

MIT
