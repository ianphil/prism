"""Custom embedding functions for the RAG feed system."""

import httpx
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """Embedding function that uses Ollama's embedding API.

    This allows users to use Ollama for embeddings instead of sentence-transformers,
    providing consistency with an Ollama-first setup.
    """

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
    ) -> None:
        """Initialize the Ollama embedding function.

        Args:
            model: The Ollama model to use for embeddings (e.g., "nomic-embed-text").
            host: The Ollama API host URL.
        """
        self.model = model
        self.host = host.rstrip("/")

    def _embed_single(self, text: str) -> list[float]:
        """Embed a single text using Ollama API.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector as a list of floats.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = httpx.post(
            f"{self.host}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of documents.

        Args:
            input: List of document texts to embed.

        Returns:
            List of embedding vectors.
        """
        return [self._embed_single(doc) for doc in input]
