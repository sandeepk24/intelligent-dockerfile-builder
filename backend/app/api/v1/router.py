"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.api.v1 import health, projects

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, tags=["projects"])
