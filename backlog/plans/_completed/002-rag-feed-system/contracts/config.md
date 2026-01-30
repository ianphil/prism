# RAGConfig Contract

## Overview

`RAGConfig` is a Pydantic model that holds configuration for the RAG feed system. It extends the existing `PrismConfig` pattern and is loaded from YAML.

## Schema

```python
from typing import Literal

from pydantic import BaseModel, Field


class RAGConfig(BaseModel):
    """Configuration for the RAG feed system."""

    collection_name: str = "posts"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: Literal["sentence-transformers", "ollama"] = "sentence-transformers"
    persist_directory: str | None = None
    feed_size: int = Field(default=5, ge=1, le=20)
    mode: Literal["preference", "random"] = "preference"
```

## Field Specifications

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `collection_name` | str | "posts" | Non-empty | ChromaDB collection name |
| `embedding_model` | str | "all-MiniLM-L6-v2" | Non-empty | Embedding model identifier |
| `embedding_provider` | Literal | "sentence-transformers" | Enum | Embedding backend |
| `persist_directory` | str \| None | None | Valid path or None | Storage directory |
| `feed_size` | int | 5 | 1-20 | Posts per feed retrieval |
| `mode` | Literal | "preference" | Enum | Default retrieval mode |

## Validation Rules

### V1: Feed size bounds

```python
feed_size: int = Field(default=5, ge=1, le=20)
```

Feed size must be between 1 and 20 inclusive.

### V2: Valid mode

```python
mode: Literal["preference", "random"] = "preference"
```

Mode must be one of the allowed values.

### V3: Valid embedding provider

```python
embedding_provider: Literal["sentence-transformers", "ollama"] = "sentence-transformers"
```

Provider must be one of the allowed values.

## YAML Configuration

### Example: Default (in-memory, sentence-transformers)

```yaml
rag:
  collection_name: posts
  embedding_model: all-MiniLM-L6-v2
  embedding_provider: sentence-transformers
  persist_directory: null
  feed_size: 5
  mode: preference
```

### Example: Persistent storage

```yaml
rag:
  collection_name: simulation_posts
  embedding_model: all-MiniLM-L6-v2
  embedding_provider: sentence-transformers
  persist_directory: ./data/chromadb
  feed_size: 10
  mode: preference
```

### Example: Ollama embeddings

```yaml
rag:
  collection_name: posts
  embedding_model: nomic-embed-text
  embedding_provider: ollama
  persist_directory: null
  feed_size: 5
  mode: preference
```

### Example: Random mode for control group

```yaml
rag:
  collection_name: posts
  embedding_model: all-MiniLM-L6-v2
  embedding_provider: sentence-transformers
  persist_directory: null
  feed_size: 5
  mode: random
```

## Integration with PrismConfig

`RAGConfig` is nested within `PrismConfig`:

```python
class PrismConfig(BaseModel):
    """Root configuration for PRISM."""

    llm: LLMConfig = LLMConfig()
    rag: RAGConfig = RAGConfig()
```

### Loading from YAML

```python
from prism.llm.config import load_config

config = load_config("configs/default.yaml")

# Access RAG settings
print(config.rag.feed_size)  # 5
print(config.rag.mode)  # "preference"
```

## Factory Function Integration

`RAGConfig` is used by `create_collection()`:

```python
from prism.rag.store import create_collection
from prism.rag.retriever import FeedRetriever

collection = create_collection(config.rag)
retriever = FeedRetriever(
    collection=collection,
    feed_size=config.rag.feed_size,
    default_mode=config.rag.mode,
)
```

## Error Messages

| Validation Failure | Error Message |
|-------------------|---------------|
| feed_size < 1 | "Input should be greater than or equal to 1" |
| feed_size > 20 | "Input should be less than or equal to 20" |
| mode invalid | "Input should be 'preference' or 'random'" |
| embedding_provider invalid | "Input should be 'sentence-transformers' or 'ollama'" |

## Environment Variable Override (Future)

The config system can be extended to support environment variables:

```python
class RAGConfig(BaseModel):
    collection_name: str = Field(default="posts", env="PRISM_RAG_COLLECTION")
    persist_directory: str | None = Field(default=None, env="PRISM_RAG_PERSIST_DIR")
    # ...
```

This is not implemented in MVP but the structure supports it.
