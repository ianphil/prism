# Post Contract

## Overview

The `Post` model represents a social media post that can be indexed in ChromaDB and retrieved for agent feeds. It follows the data structure specified in PRD §4.4.

## Schema

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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

    # Engagement metrics
    likes: int = Field(default=0, ge=0)
    reshares: int = Field(default=0, ge=0)
    replies: int = Field(default=0, ge=0)
    velocity: float = Field(default=0.0, ge=0.0)
```

## Field Specifications

### Core Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | str | Non-empty | Unique identifier for the post |
| `author_id` | str | Non-empty | ID of the creating agent |
| `text` | str | Non-empty | Post content (used for embedding) |
| `timestamp` | datetime | Valid datetime | When the post was created |

### Media Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `has_media` | bool | - | Whether post contains visual media |
| `media_type` | str \| None | "image", "video", "gif", or None | Type of attached media |
| `media_description` | str \| None | - | Alt text / description of media |

### Engagement Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `likes` | int | >= 0 | Number of likes |
| `reshares` | int | >= 0 | Number of reshares |
| `replies` | int | >= 0 | Number of replies |
| `velocity` | float | >= 0.0 | Engagement rate over time |

## Validation Rules

### V1: Non-empty identifiers

```python
@field_validator("id", "author_id", "text")
@classmethod
def must_be_non_empty(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("field must be non-empty")
    return v
```

### V2: Media type consistency

```python
@field_validator("media_type")
@classmethod
def media_type_requires_has_media(cls, v, info):
    if v is not None and not info.data.get("has_media", False):
        raise ValueError("media_type set but has_media is False")
    return v
```

## Methods

### to_metadata()

Converts Post to ChromaDB metadata dict.

```python
def to_metadata(self) -> dict:
    """Convert to ChromaDB-compatible metadata dict."""
    return {
        "author_id": self.author_id,
        "timestamp": self.timestamp.isoformat(),
        "has_media": self.has_media,
        "media_type": self.media_type,
        "media_description": self.media_description,
        "likes": self.likes,
        "reshares": self.reshares,
        "replies": self.replies,
        "velocity": self.velocity,
    }
```

### from_chroma_result() (class method)

Reconstructs Post from ChromaDB query result.

```python
@classmethod
def from_chroma_result(
    cls,
    id: str,
    document: str,
    metadata: dict
) -> "Post":
    """Reconstruct Post from ChromaDB result."""
    return cls(
        id=id,
        text=document,
        author_id=metadata["author_id"],
        timestamp=datetime.fromisoformat(metadata["timestamp"]),
        has_media=metadata.get("has_media", False),
        media_type=metadata.get("media_type"),
        media_description=metadata.get("media_description"),
        likes=metadata.get("likes", 0),
        reshares=metadata.get("reshares", 0),
        replies=metadata.get("replies", 0),
        velocity=metadata.get("velocity", 0.0),
    )
```

## Usage Examples

### Creating a post

```python
from datetime import datetime
from prism.rag.models import Post

post = Post(
    id="post_001",
    author_id="agent_42",
    text="My local coffee shop now accepts Bitcoin!",
    timestamp=datetime.now(),
    has_media=True,
    media_type="image",
    media_description="Bitcoin payment terminal at counter",
    likes=89,
    reshares=34,
    replies=12,
)
```

### Converting for ChromaDB

```python
# For upsert
collection.upsert(
    ids=[post.id],
    documents=[post.text],
    metadatas=[post.to_metadata()],
)
```

### Reconstructing from ChromaDB

```python
result = collection.get(ids=["post_001"], include=["documents", "metadatas"])
post = Post.from_chroma_result(
    id=result["ids"][0],
    document=result["documents"][0],
    metadata=result["metadatas"][0],
)
```
