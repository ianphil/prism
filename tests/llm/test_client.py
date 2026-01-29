"""Tests for create_llm_client factory function."""

from unittest.mock import MagicMock, patch

from prism.llm.config import LLMConfig


class TestCreateLlmClient:
    """Tests for create_llm_client factory function."""

    def test_creates_ollama_chat_client(self):
        """create_llm_client returns an OllamaChatClient instance."""
        from prism.llm.client import create_llm_client

        config = LLMConfig()
        client = create_llm_client(config)

        # Verify it's an OllamaChatClient
        from agent_framework.ollama import OllamaChatClient

        assert isinstance(client, OllamaChatClient)

    def test_passes_host_from_config(self):
        """create_llm_client passes host from config to OllamaChatClient."""
        from prism.llm.client import create_llm_client

        config = LLMConfig(host="http://custom-host:11434")

        with patch(
            "prism.llm.client.OllamaChatClient", autospec=True
        ) as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            create_llm_client(config)

            mock_client_cls.assert_called_once()
            call_kwargs = mock_client_cls.call_args.kwargs
            assert call_kwargs["host"] == "http://custom-host:11434"

    def test_passes_model_id_from_config(self):
        """create_llm_client passes model_id from config to OllamaChatClient."""
        from prism.llm.client import create_llm_client

        config = LLMConfig(model_id="qwen2.5")

        with patch(
            "prism.llm.client.OllamaChatClient", autospec=True
        ) as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            create_llm_client(config)

            mock_client_cls.assert_called_once()
            call_kwargs = mock_client_cls.call_args.kwargs
            assert call_kwargs["model_id"] == "qwen2.5"

    def test_default_config_uses_localhost_and_mistral(self):
        """create_llm_client with default config uses localhost:11434 and mistral."""
        from prism.llm.client import create_llm_client

        config = LLMConfig()  # All defaults

        with patch(
            "prism.llm.client.OllamaChatClient", autospec=True
        ) as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            create_llm_client(config)

            call_kwargs = mock_client_cls.call_args.kwargs
            assert call_kwargs["host"] == "http://localhost:11434"
            assert call_kwargs["model_id"] == "mistral"
