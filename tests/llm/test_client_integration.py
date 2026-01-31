"""Integration tests for LLM client with real Ollama.

These tests require a running Ollama instance with the mistral model.
Run with: uv run pytest -m integration
"""

import json

import pytest

from prism.llm.client import create_llm_client
from prism.llm.config import LLMConfig, load_config


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests that require a running Ollama server."""

    def test_client_connects_to_ollama(self):
        """Verify OllamaChatClient can connect to local Ollama."""
        config = LLMConfig(model_id="mistral")
        client = create_llm_client(config)

        # Client should be created without error
        assert client is not None
        assert client.host == "http://localhost:11434"
        assert client.model_id == "mistral"

    @pytest.mark.asyncio
    async def test_agent_returns_response(self):
        """Verify ChatAgent can get a response from Ollama."""
        config = load_config("configs/default.yaml")
        client = create_llm_client(config.llm)

        # Create a simple agent using as_agent()
        agent = client.as_agent(
            name="test_agent",
            instructions="You are a helpful assistant. Be brief.",
        )

        # Get a response
        response = await agent.run(
            "Say hello in exactly 3 words.",
            options={"max_tokens": 50},
        )

        # Verify we got a response
        assert response is not None
        assert response.text is not None
        assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_agent_with_config_from_yaml(self):
        """Verify full config-to-response flow works."""
        # Load config from default YAML
        config = load_config("configs/default.yaml")
        client = create_llm_client(config.llm)

        agent = client.as_agent(
            name="config_test_agent",
            instructions="You are a helpful assistant. Respond with one word only.",
        )

        response = await agent.run(
            "What color is the sky? One word.",
            options={
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
            },
        )

        assert response is not None
        assert response.text is not None
        # Should be a short response given the constraints
        assert len(response.text.strip()) > 0

    @pytest.mark.asyncio
    async def test_json_format_with_manual_parsing(self):
        """Verify JSON format mode works for structured output.

        Ollama doesn't support Pydantic response_format directly,
        so we use format='json' and parse manually. This validates
        the fallback strategy documented in plan.md.
        """
        from pydantic import BaseModel

        class SimpleResponse(BaseModel):
            answer: str
            confidence: int

        config = load_config("configs/default.yaml")
        client = create_llm_client(config.llm)

        agent = client.as_agent(
            name="structured_agent",
            instructions=(
                "Answer questions. Return JSON with 'answer' (string) "
                "and 'confidence' (1-10 integer). Only output valid JSON."
            ),
        )

        response = await agent.run(
            "What is 2+2?",
            options={"response_format": "json", "max_tokens": 100},
        )

        # Verify we got JSON text
        assert response.text is not None
        assert len(response.text) > 0

        # Parse into Pydantic model (this is the fallback strategy)
        parsed_json = json.loads(response.text)
        result = SimpleResponse(**parsed_json)

        assert result.answer is not None
        assert isinstance(result.confidence, int)
