"""Ollama REST API client."""

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Async client for the Ollama REST API."""

    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.ollama_timeout

    async def is_connected(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/version")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.warning("Ollama server not reachable at %s", self.base_url)
            return False

    async def list_models(self) -> list[dict]:
        """List locally available models."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return data.get("models", [])
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            logger.error("Failed to list Ollama models: %s", exc)
            return []

    async def generate(self, model: str, prompt: str, system: str | None = None) -> str:
        """Generate a completion from Ollama (non-streaming)."""
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")


ollama_client = OllamaClient()
