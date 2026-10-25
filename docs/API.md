# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

## Health & Discovery

### GET /health
Check backend and Ollama connectivity.

### GET /models
List available Ollama models.

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
Poll generation or optimize status (`pending`, `running`, `completed`, `failed`).

### GET /dockerfiles/{id}
Retrieve a generated or optimized Dockerfile, original file (if any), issues, `.dockerignore`, explanation, and decisions.

### PUT /dockerfiles/{id}
Save user edits to Dockerfile and/or `.dockerignore`.

### GET /dockerfiles/history
List previously generated Dockerfiles for this process. Persistence is in-memory until Milestone 4.

### POST /dockerfiles/{id}/validate
Not implemented until Milestone 3.

### POST /dockerfiles/{id}/repair
Not implemented until Milestone 3.

## Settings

### GET /settings
Return current application settings.

### PUT /settings
Update Ollama endpoint, default model, timeout, and max repair attempts.
