"""LLM client factory functions."""

from agent_framework.ollama import OllamaChatClient

from prism.llm.config import LLMConfig


def create_llm_client(config: LLMConfig) -> OllamaChatClient:
    """Create an OllamaChatClient from validated configuration.

    Args:
        config: Validated LLM configuration.

    Returns:
        Configured OllamaChatClient instance.
    """
    return OllamaChatClient(
        host=config.host,
        model_id=config.model_id,
    )
