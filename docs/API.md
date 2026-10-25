# API Reference

Base URL: `http://localhost:8000/api/v1`

## Health & Discovery

### GET /health
Check backend and Ollama connectivity.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "ollama_connected": true,
  "ollama_url": "http://localhost:11434"
}
```

### GET /models
List available Ollama models.

**Response 200:**
```json
{
  "models": [
    {
      "name": "codellama:7b",
      "size": 3826793472,
      "modified_at": "2024-01-15T10:30:00Z"
    }
  ],
  "default_model": "codellama:7b"
}
```

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

**Request (multipart — ZIP upload):**
- `file`: ZIP file (max 50MB)

**Response 200:**
```json
{
  "project_id": "uuid",
  "language": "python",
  "framework": "fastapi",
  "entry_point": "app/main.py",
  "dependencies": ["fastapi", "uvicorn"],
  "python_version": "3.12",
  "ports": [8000],
  "has_dockerfile": false,
  "file_tree": ["app/", "app/main.py", "requirements.txt"]
}
```

## Dockerfiles

### POST /dockerfiles/generate
Generate a Dockerfile from project analysis.

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
  "status": "pending"
}
```

### GET /dockerfiles/{id}
Retrieve a generated Dockerfile.

### PUT /dockerfiles/{id}
Update Dockerfile content (user edits).

### POST /dockerfiles/{id}/validate
Run validation pipeline on a Dockerfile.

### POST /dockerfiles/{id}/repair
Trigger AI repair for a failed validation.

### GET /dockerfiles/history
List previously generated Dockerfiles.

## Validations

### GET /validations/{id}
Retrieve validation results.

## Settings

### GET /settings
Get current application settings.

### PUT /settings
Update application settings.
