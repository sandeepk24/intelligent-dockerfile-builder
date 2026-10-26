"""Test doubles for inference providers."""

from typing import Any


class FakeLLMProvider:
    """Deterministic LLM used in tests — never calls a real model."""

    def __init__(self, connected: bool = True) -> None:
        self.connected = connected
        self.prompts: list[str] = []

    async def is_connected(self) -> bool:
        return self.connected

    async def list_models(self) -> list[dict[str, Any]]:
        return [{"name": "codellama:7b", "size": 1}]

    async def generate(self, model: str, prompt: str, system: str | None = None) -> str:
        return ""

    async def generate_json(
        self, model: str, prompt: str, system: str | None = None
    ) -> dict[str, Any]:
        self.prompts.append(prompt)
        payload = {
            "dockerfile": (
                "FROM python:3.12-slim\n"
                "WORKDIR /app\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\n"
                "RUN useradd --create-home appuser\n"
                "USER appuser\n"
                "EXPOSE 8000\n"
                'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
            ),
            "explanation": "Slim Python image with dependency caching and a non-root user.",
            "decisions": ["Use python:3.12-slim", "Install deps before copying source"],
            "issues": [],
        }
        if "<build_log>" in prompt:
            payload["root_cause"] = (
                "Base image tag could not be pulled or a RUN instruction failed."
            )
            payload["explanation"] = "Corrected the failing RUN layer and kept a non-root user."
            payload["decisions"] = ["Fix the failing build instruction", "Keep USER appuser"]
        if "Known issues from static review" in prompt:
            payload["explanation"] = (
                "Replaced python:latest, dropped root, stopped copying .env, and pinned a slim base image."
            )
            payload["decisions"] = [
                "Pin python:3.12-slim instead of latest",
                "Do not copy .env into the image",
                "Run as a non-root user",
            ]
        return payload
