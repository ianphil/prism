"""Data models for the RAG feed system."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Post(BaseModel):
    """A social media post with content, media, and engagement metrics."""

    # Core fields
    id: str
    author_id: str
    text: str
    timestamp: datetime

    # Media simulation
    has_media: bool = False
    media_type: Literal["image", "video", "gif"] | None = None
    media_description: str | None = None

    # Reply chain
    parent_id: str | None = None

    # Engagement metrics
    likes: int = Field(default=0, ge=0)
    reshares: int = Field(default=0, ge=0)
    replies: int = Field(default=0, ge=0)
    velocity: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def validate_media_consistency(self) -> "Post":
        """Ensure media_type is only set when has_media is True."""
        if not self.has_media and self.media_type is not None:
            raise ValueError("media_type cannot be set when has_media is False")
        return self

    def to_metadata(self) -> dict:
        """Convert to ChromaDB-compatible metadata dict.

        Returns:
            Dict with all fields except id and text (stored separately in ChromaDB).
        """
        return {
            "author_id": self.author_id,
            "timestamp": self.timestamp.isoformat(),
            "has_media": self.has_media,
            "media_type": self.media_type,
            "media_description": self.media_description,
            "parent_id": self.parent_id,
            "likes": self.likes,
            "reshares": self.reshares,
            "replies": self.replies,
            "velocity": self.velocity,
        }

    @classmethod
    def from_chroma_result(
        cls,
        id: str,
        document: str,
        metadata: dict,
    ) -> "Post":
        """Reconstruct Post from ChromaDB result.

        Args:
            id: The document ID from ChromaDB.
            document: The document text (post content).
            metadata: The metadata dict from ChromaDB.

        Returns:
            Reconstructed Post instance.
        """
        return cls(
            id=id,
            text=document,
            author_id=metadata["author_id"],
            timestamp=datetime.fromisoformat(metadata["timestamp"]),
            has_media=metadata.get("has_media", False),
            media_type=metadata.get("media_type"),
            media_description=metadata.get("media_description"),
            parent_id=metadata.get("parent_id"),
            likes=metadata.get("likes", 0),
            reshares=metadata.get("reshares", 0),
            replies=metadata.get("replies", 0),
            velocity=metadata.get("velocity", 0.0),
        )
