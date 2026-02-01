"""Configuration for the RAG feed system."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

EmbeddingProvider = Literal["sentence-transformers", "ollama"]
RankingMode = Literal["x_algo", "preference", "random"]


class RankingConfig(BaseModel):
    """Configuration for X algorithm ranking."""

    mode: RankingMode = "preference"
    out_of_network_scale: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Multiplicative penalty for out-of-network posts",
    )
    reply_scale: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Multiplicative penalty for reply posts",
    )
    author_diversity_decay: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Exponential decay factor per author occurrence",
    )
    author_diversity_floor: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum score after author diversity decay",
    )
    in_network_limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum in-network candidates to consider",
    )
    out_of_network_limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum out-of-network candidates to consider",
    )

    @model_validator(mode="after")
    def validate_floor_less_than_decay(self) -> "RankingConfig":
        """Ensure floor doesn't exceed decay factor."""
        if self.author_diversity_floor > self.author_diversity_decay:
            raise ValueError(
                f"author_diversity_floor ({self.author_diversity_floor}) "
                f"must be <= author_diversity_decay ({self.author_diversity_decay})"
            )
        return self


class RAGConfig(BaseModel):
    """Configuration for the RAG feed system."""

    collection_name: str = "posts"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: EmbeddingProvider = "sentence-transformers"
    persist_directory: str | None = None
    feed_size: int = Field(default=5, ge=1, le=20)
    mode: Literal["preference", "random"] = "preference"
    ollama_timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
