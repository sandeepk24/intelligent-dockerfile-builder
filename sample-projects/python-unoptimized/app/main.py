"""Sample FastAPI app shipped with an unoptimized Dockerfile for review demos."""

from fastapi import FastAPI

app = FastAPI(title="Legacy Sample API")


@app.get("/")
async def root():
    return {"message": "Hello from an unoptimized container"}


@app.get("/health")
async def health():
    return {"status": "ok"}
