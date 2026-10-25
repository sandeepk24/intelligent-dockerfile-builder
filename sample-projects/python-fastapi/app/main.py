"""Sample FastAPI application for testing Dockerfile generation."""

from fastapi import FastAPI

app = FastAPI(title="Sample API", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}


@app.get("/health")
async def health():
    return {"status": "ok"}
