"""ChromaDB collection factory for the RAG feed system."""

import chromadb
from chromadb.api.types import EmbeddingFunction
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from prism.rag.config import RAGConfig
from prism.rag.embeddings import OllamaEmbeddingFunction

# Module-level client cache for get_or_create semantics
_clients: dict[str | None, chromadb.ClientAPI] = {}


def _get_client(persist_directory: str | None) -> chromadb.ClientAPI:
    """Get or create a ChromaDB client for the given persistence setting.

    Args:
        persist_directory: Path for persistent storage, or None for in-memory.

    Returns:
        ChromaDB client instance.
    """
    if persist_directory not in _clients:
        if persist_directory is None:
            _clients[persist_directory] = chromadb.Client()
        else:
            _clients[persist_directory] = chromadb.PersistentClient(
                path=persist_directory
            )
    return _clients[persist_directory]


def _get_embedding_function(config: RAGConfig) -> EmbeddingFunction:
    """Get the appropriate embedding function based on config.

    Args:
        config: RAG configuration with embedding provider and model settings.

    Returns:
        Configured embedding function.
    """
    if config.embedding_provider == "sentence-transformers":
        return SentenceTransformerEmbeddingFunction(model_name=config.embedding_model)
    elif config.embedding_provider == "ollama":
        return OllamaEmbeddingFunction(model=config.embedding_model)
    else:
        raise ValueError(f"Unknown embedding provider: {config.embedding_provider}")


def create_collection(config: RAGConfig) -> chromadb.Collection:
    """Create or get a ChromaDB collection from configuration.

    Args:
        config: RAG configuration specifying collection name, embedding model,
            and persistence settings.

    Returns:
        ChromaDB collection with embedding function configured.
    """
    client = _get_client(config.persist_directory)
    embedding_function = _get_embedding_function(config)

    return client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=embedding_function,
    )
