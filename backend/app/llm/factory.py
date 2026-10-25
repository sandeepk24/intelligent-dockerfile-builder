"""Factory for the configured LLM provider."""

from app.llm.ollama_client import ollama_client
from app.llm.provider import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the active inference provider.

    Ollama is the default local implementation. Swap this function to use
    Amazon Bedrock or another provider without changing application services.
    """
    return ollama_client
