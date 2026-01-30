"""Custom embedding functions for the RAG feed system."""

import httpx
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """Embedding function that uses Ollama's embedding API.

    This allows users to use Ollama for embeddings instead of sentence-transformers,
    providing consistency with an Ollama-first setup.
    """

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Ollama embedding function.

        Args:
            model: The Ollama model to use for embeddings (e.g., "nomic-embed-text").
            host: The Ollama API host URL.
            timeout: Request timeout in seconds (default: 30.0).
        """
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    def _embed_single(self, text: str) -> list[float]:
        """Embed a single text using Ollama API.

        Retries up to 3 times with exponential backoff on transient failures
        (timeouts and network errors).

        Args:
            text: The text to embed.

        Returns:
            The embedding vector as a list of floats.

        Raises:
            httpx.HTTPError: If the API request fails after retries.
        """
        response = httpx.post(
            f"{self.host}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=self.timeout,
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
