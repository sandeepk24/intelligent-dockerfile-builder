"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.api.v1 import dockerfiles, health, projects, settings, validations

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(dockerfiles.router, tags=["dockerfiles"])
api_router.include_router(validations.router, tags=["validations"])
api_router.include_router(settings.router, tags=["settings"])
