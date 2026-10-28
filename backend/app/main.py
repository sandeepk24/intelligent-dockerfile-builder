"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.store import configure_persistence

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_application: FastAPI):
    configure_persistence()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    @application.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"},
        )

    return application


app = create_app()
