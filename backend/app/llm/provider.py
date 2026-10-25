"""LLM provider interface.

Application services depend on this protocol, not on Ollama specifically.
A Bedrock, vLLM, or OpenAI-compatible provider can implement the same contract.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Inference provider used for Dockerfile generation and repair."""

    @abstractmethod
    async def is_connected(self) -> bool:
        """Return True when the inference service is reachable."""

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """Return locally available models."""

    @abstractmethod
    async def generate(self, model: str, prompt: str, system: str | None = None) -> str:
        """Return a raw text completion."""

    @abstractmethod
    async def generate_json(
        self, model: str, prompt: str, system: str | None = None
    ) -> dict[str, Any]:
        """Return a JSON object from a structured generation call."""
