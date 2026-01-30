"""Configuration for the RAG feed system."""

from typing import Literal

from pydantic import BaseModel, Field

EmbeddingProvider = Literal["sentence-transformers", "ollama"]


class RAGConfig(BaseModel):
    """Configuration for the RAG feed system."""

    collection_name: str = "posts"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: EmbeddingProvider = "sentence-transformers"
    persist_directory: str | None = None
    feed_size: int = Field(default=5, ge=1, le=20)
    mode: Literal["preference", "random"] = "preference"
