# Architecture

## Overview

The AI Dockerfile Builder follows a clean layered architecture with strict separation between presentation, business logic, LLM integration, and infrastructure concerns.

## System Components

### Frontend (React + Vite SPA)

```
frontend/src/
├── api/           # API client layer (typed HTTP calls)
├── components/    # Reusable UI components
│   ├── layout/    # Shell, sidebar, navigation
│   ├── dockerfile/# Monaco editor, validation results
│   └── common/    # Buttons, cards, loaders, toasts
├── pages/         # Route-level page components
├── hooks/         # Custom React hooks
├── types/         # TypeScript type definitions
├── lib/           # Utilities and helpers
├── App.tsx        # Root component with routing
└── main.tsx       # Entry point
```

- TanStack Query manages server state (caching, refetching, optimistic updates)
- React Router handles client-side navigation
- Monaco Editor provides Dockerfile editing with syntax highlighting
- All API calls go through a typed client layer — no fetch() scattered in components

### Backend (FastAPI)

```
backend/app/
├── api/v1/        # Versioned REST endpoints
├── core/          # Configuration, security, dependencies
├── analyzers/     # Language/framework detection
├── llm/           # Ollama client abstraction
├── generators/    # Dockerfile + .dockerignore generation
├── validators/    # Hadolint, Docker build, Trivy
├── evaluators/    # Build metrics collection
├── services/      # Business logic orchestration
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response schemas
├── db/            # Database session and migrations
└── main.py        # FastAPI application factory
```

### Key Design Decisions

1. **LLM Abstraction**: The `llm/` module defines a provider interface. Ollama is the default implementation. This allows future replacement with Bedrock, vLLM, or any OpenAI-compatible API.

2. **Async Throughout**: All I/O operations (HTTP to Ollama, Docker commands, file reads) use async/await. CPU-bound analysis runs in thread pool executors.

3. **Background Jobs**: LLM generation and Docker builds run as background tasks. The API returns a job ID immediately; the frontend polls for status.

4. **Security Boundaries**:
   - Workspace root is explicitly configured — no arbitrary filesystem access
   - ZIP uploads validated against traversal, symlinks, bombs
   - Docker builds require explicit approval and run with resource limits
   - LLM prompts treat uploaded code as data, never as instructions
   - CORS restricted to configured origins

## Data Flow

```
User Action → React UI → API Client → FastAPI Endpoint
                                           ↓
                                    Pydantic Validation
                                           ↓
                                     Service Layer
                                      ↙    ↓     ↘
                              Analyzer  LLM Client  Validator
                                           ↓
                                    SQLite Storage
                                           ↓
                                   Response Schema
                                           ↓
                              API Response → React UI
```

## Database Schema (SQLite)

- **projects**: Analyzed project metadata
- **dockerfiles**: Generated Dockerfile content and metadata
- **validations**: Build/lint/scan results per Dockerfile
- **repairs**: AI repair attempts linked to validations
- **evaluations**: Aggregated metrics per generation

## API Versioning

All endpoints are prefixed with `/api/v1/`. Breaking changes require a new version prefix.
