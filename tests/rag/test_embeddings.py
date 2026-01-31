"""Tests for Ollama embedding function."""

from unittest.mock import MagicMock, patch

import httpx
import pytest


class TestOllamaEmbeddingFunction:
    """Tests for OllamaEmbeddingFunction class."""

    def test_implements_embedding_function_protocol(self):
        """OllamaEmbeddingFunction implements chromadb embedding function protocol."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")

        # Must be callable with a list of documents
        assert callable(ef)

    def test_returns_list_of_embeddings(self):
        """Calling the function returns a list of embedding vectors."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")

        # Mock the Ollama API call
        mock_embedding = [0.1, 0.2, 0.3] * 128  # 384-dim vector

        with patch.object(ef, "_embed_single", return_value=mock_embedding):
            result = ef(["Hello world", "Test document"])

        assert isinstance(result, list)
        assert len(result) == 2
        # Each embedding should be a sequence of floats
        assert all(len(emb) == len(mock_embedding) for emb in result)

    def test_uses_configured_model(self):
        """OllamaEmbeddingFunction uses the model specified in constructor."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        assert ef.model == "nomic-embed-text"

        ef2 = OllamaEmbeddingFunction(model="mxbai-embed-large")
        assert ef2.model == "mxbai-embed-large"

    def test_uses_configured_host(self):
        """OllamaEmbeddingFunction uses the host specified in constructor."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(
            model="nomic-embed-text", host="http://custom:11434"
        )
        assert ef.host == "http://custom:11434"

    def test_default_host_is_localhost(self):
        """Default host is localhost:11434."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        assert ef.host == "http://localhost:11434"

    def test_default_timeout_is_30_seconds(self):
        """Default timeout is 30 seconds."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        assert ef.timeout == 30.0

    def test_uses_configured_timeout(self):
        """OllamaEmbeddingFunction uses the timeout specified in constructor."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text", timeout=60.0)
        assert ef.timeout == 60.0

    def test_retries_on_timeout_then_succeeds(self):
        """_embed_single retries on timeout and succeeds on subsequent attempt."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        mock_embedding = [0.1, 0.2, 0.3]

        # Create a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embedding": mock_embedding}

        # First call raises timeout, second succeeds
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("Connection timed out")
            return mock_response

        with patch("httpx.post", side_effect=side_effect):
            result = ef._embed_single("test text")

        assert result == mock_embedding
        assert call_count == 2  # First attempt failed, second succeeded

    def test_retries_on_network_error_then_succeeds(self):
        """_embed_single retries on network error and succeeds on subsequent attempt."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        mock_embedding = [0.4, 0.5, 0.6]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embedding": mock_embedding}

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.NetworkError("Connection refused")
            return mock_response

        with patch("httpx.post", side_effect=side_effect):
            result = ef._embed_single("test text")

        assert result == mock_embedding
        assert call_count == 2

    def test_raises_after_max_retries(self):
        """_embed_single raises after exhausting retries."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")

        with patch("httpx.post", side_effect=httpx.TimeoutException("Timeout")):
            with pytest.raises(httpx.TimeoutException):
                ef._embed_single("test text")

    @pytest.mark.integration
    def test_calls_ollama_api(self):
        """Integration test: actually calls Ollama API (requires running Ollama)."""
        from prism.llm.config import load_config
        from prism.rag.embeddings import OllamaEmbeddingFunction

        config = load_config("configs/default.yaml")
        ef = OllamaEmbeddingFunction(model="nomic-embed-text", host=config.llm.host)
        result = ef(["Hello world"])

        # Should return a list with one embedding vector
        assert isinstance(result, list)
        assert len(result) == 1
        # ChromaDB returns numpy arrays or lists depending on version
        assert hasattr(result[0], "__len__")
        assert len(result[0]) > 0  # Should have dimensions
