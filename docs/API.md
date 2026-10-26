# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

## Health & Discovery

### GET /health
Check backend, Ollama, Docker, Hadolint, and Trivy availability.

### GET /models
List available Ollama models.

### GET /stats
In-memory session metrics: generated Dockerfiles, validation counts, successful builds, average build time, and repairs.

## Workspace

### GET /workspace/projects
List directories under the configured `WORKSPACE_ROOT`. Paths outside that root are never returned.

## Projects

### POST /projects/analyze
Analyze a project directory or uploaded ZIP.

**Request (JSON — local directory):**
```json
{
  "source_type": "directory",
  "path": "python-fastapi"
}
```

`path` is relative to `WORKSPACE_ROOT`. Absolute paths and `..` are rejected.

**Request (JSON — pasted Dockerfile):**
```json
{
  "source_type": "dockerfile",
  "name": "legacy",
  "dockerfile": "FROM python:latest\nCMD python app.py\n"
}
```

Static issues are returned in `dockerfile_issues` without calling the LLM.

**Request (multipart — ZIP or Dockerfile upload):**
- `file`: ZIP archive or a file named `Dockerfile`

ZIP members are rejected for path traversal, symlinks, oversize archives, and high compression ratios.

**Response 200:**
```json
{
  "project_id": "uuid",
  "name": "python-fastapi",
  "source_type": "directory",
  "language": "python",
  "framework": "fastapi",
  "entry_point": "app/main.py",
  "runtime_version": "3.12",
  "dependencies": ["fastapi", "uvicorn"],
  "ports": [8000],
  "build_command": "pip install --no-cache-dir -r requirements.txt",
  "start_command": "uvicorn app.main:app --host 0.0.0.0 --port 8000",
  "has_dockerfile": false,
  "file_tree": ["app/__init__.py", "app/main.py", "requirements.txt"]
}
```

### GET /projects/{project_id}
Retrieve a previously analyzed project.

## Dockerfiles

### POST /dockerfiles/generate
Start a background generation job. The HTTP response returns immediately.

**Request:**
```json
{
  "project_id": "uuid",
  "model": "codellama:7b",
  "instructions": "Use Alpine base image"
}
```

**Response 202:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "job_type": "generate",
  "dockerfile_id": null,
  "error": null
}
```

### POST /dockerfiles/optimize
Review an existing Dockerfile and generate an optimized rewrite. Uses the project's Dockerfile unless `dockerfile` is provided.

**Request:**
```json
{
  "project_id": "uuid",
  "dockerfile": "FROM python:latest\\n...",
  "model": "codellama:7b",
  "instructions": "Prefer distroless"
}
```

**Response 202:** job ID with `job_type: "optimize"`.

### GET /jobs/{job_id}
Poll generation, optimize, validation, or repair status (`pending`, `running`, `completed`, `failed`). Completed validation jobs include `validation_id`.

### GET /dockerfiles/{id}
Retrieve a generated or optimized Dockerfile, original file (if any), issues, `.dockerignore`, explanation, and decisions.

### PUT /dockerfiles/{id}
Save user edits to Dockerfile and/or `.dockerignore`.

### GET /dockerfiles/history
List previously generated Dockerfiles for this process. Persistence is in-memory until Milestone 4.

### POST /dockerfiles/{id}/validate
Start a background validation job. Lint (Hadolint + static review) always runs. A Docker build runs only when both flags are true.

**Request:**
```json
{
  "approve_build": true,
  "confirm_untrusted_execution": true,
  "run_trivy": false,
  "run_startup_check": true
}
```

**Response 202:** job ID with `job_type: "validate"`. `approve_build` without `confirm_untrusted_execution` returns 400.

### GET /dockerfiles/{id}/validations
List validation runs for a Dockerfile, newest first.

### GET /validations/{id}
Fetch one validation: lint, build, image size, duration, optional Trivy and startup results, and a sanitized error log.

### POST /dockerfiles/{id}/repair
Propose a repaired Dockerfile from a **failed** validation. Does not auto-rebuild. Lineage is capped at `MAX_REPAIR_ATTEMPTS` (default 3).

**Request:**
```json
{
  "validation_id": "uuid",
  "model": "codellama:7b",
  "instructions": "Keep python:3.12-slim"
}
```

**Response 202:** job ID with `job_type: "repair"`. On completion, `dockerfile_id` points at the new repaired file.

### GET /dockerfiles/{id}/repairs
Repair history for this Dockerfile, including `attempts_used` and `max_attempts`.

## Settings

### GET /settings
Return current application settings.

### PUT /settings
Update Ollama endpoint, default model, timeout, and max repair attempts.
