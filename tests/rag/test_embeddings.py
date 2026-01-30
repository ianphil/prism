"""Tests for Ollama embedding function."""

from unittest.mock import patch

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

    @pytest.mark.integration
    def test_calls_ollama_api(self):
        """Integration test: actually calls Ollama API (requires running Ollama)."""
        from prism.rag.embeddings import OllamaEmbeddingFunction

        ef = OllamaEmbeddingFunction(model="nomic-embed-text")
        result = ef(["Hello world"])

        # Should return a list with one embedding vector
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) > 0  # Should have dimensions
        assert all(isinstance(x, float) for x in result[0])
