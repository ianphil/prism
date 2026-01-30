# FeedRetriever Contract

## Overview

`FeedRetriever` is the main interface for indexing posts and retrieving feeds from ChromaDB. It encapsulates all vector store operations behind a simple API.

## Interface

```python
from typing import Literal

from prism.rag.models import Post


class FeedRetriever:
    """Retrieves feeds from ChromaDB based on agent interests or random sampling."""

    def __init__(
        self,
        collection: chromadb.Collection,
        feed_size: int = 5,
        default_mode: Literal["preference", "random"] = "preference",
    ) -> None:
        """Initialize with a ChromaDB collection.

        Args:
            collection: ChromaDB collection with embedding function configured.
            feed_size: Number of posts to return per feed (1-20).
            default_mode: Default retrieval mode if not specified in get_feed().
        """
        ...

    def add_post(self, post: Post) -> None:
        """Index a single post in the collection.

        Args:
            post: Post to index.

        Raises:
            ValueError: If post validation fails.
        """
        ...

    def add_posts(self, posts: list[Post]) -> None:
        """Index multiple posts in the collection.

        Args:
            posts: List of posts to index.

        Raises:
            ValueError: If any post validation fails.
        """
        ...

    def get_feed(
        self,
        interests: list[str] | None = None,
        mode: Literal["preference", "random"] | None = None,
    ) -> list[Post]:
        """Retrieve a feed of posts.

        Args:
            interests: Agent interests for preference mode (required if mode="preference").
            mode: Retrieval mode. Uses default_mode if None.

        Returns:
            List of Post objects (up to feed_size).

        Raises:
            ValueError: If mode="preference" and interests is None or empty.
            RuntimeError: If collection is empty.
        """
        ...

    def count(self) -> int:
        """Return the number of indexed posts."""
        ...

    def clear(self) -> None:
        """Remove all posts from the collection."""
        ...
```

## Behavior Specifications

### B1: Preference Mode Retrieval

When `mode="preference"`:

1. `interests` must be provided and non-empty
2. Interests are joined into a query string: `"crypto technology startups"`
3. Query embedding is computed via collection's embedding function
4. ChromaDB returns `n_results=feed_size` most similar posts
5. Results are converted to `Post` objects and returned

```python
def get_feed(self, interests=["crypto", "tech"], mode="preference"):
    query_text = " ".join(interests)
    results = self._collection.query(
        query_texts=[query_text],
        n_results=self._feed_size,
        include=["documents", "metadatas"],
    )
    return self._results_to_posts(results)
```

### B2: Random Mode Retrieval

When `mode="random"`:

1. `interests` is ignored
2. All post IDs are retrieved from collection
3. `feed_size` IDs are randomly sampled (or all if fewer exist)
4. Sampled posts are retrieved by ID
5. Results are converted to `Post` objects and returned

```python
def get_feed(self, interests=None, mode="random"):
    all_data = self._collection.get()
    all_ids = all_data["ids"]
    sample_size = min(self._feed_size, len(all_ids))
    sampled_ids = random.sample(all_ids, sample_size)
    results = self._collection.get(
        ids=sampled_ids,
        include=["documents", "metadatas"],
    )
    return self._results_to_posts(results)
```

### B3: Post Indexing

When `add_post(post)` is called:

1. Post is validated (Pydantic)
2. `collection.upsert()` is called with:
   - `ids=[post.id]`
   - `documents=[post.text]`
   - `metadatas=[post.to_metadata()]`
3. If `post.id` already exists, it is updated (upsert semantics)

### B4: Empty Collection Handling

- `get_feed()` on an empty collection raises `RuntimeError("Collection is empty")`
- `count()` returns 0 for empty collection
- `clear()` on empty collection is a no-op

### B5: Feed Size Bounds

- If collection has fewer posts than `feed_size`, all posts are returned
- `feed_size` is clamped to valid range (1-20) in constructor

## Error Handling

| Scenario | Error | Message |
|----------|-------|---------|
| Preference mode without interests | ValueError | "interests required for preference mode" |
| Empty interests list | ValueError | "interests must be non-empty" |
| Empty collection | RuntimeError | "Collection is empty" |
| Invalid feed_size | ValueError | "feed_size must be between 1 and 20" |

## Thread Safety

`FeedRetriever` is **not** thread-safe. For concurrent access:
- Use separate `FeedRetriever` instances per thread, or
- Add external synchronization

ChromaDB itself handles internal locking for persistent storage.

## Usage Examples

### Basic usage

```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import chromadb

# Setup
client = chromadb.Client()
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.create_collection("posts", embedding_function=embedding_fn)

retriever = FeedRetriever(collection, feed_size=5, default_mode="preference")

# Index posts
retriever.add_posts(posts)

# Retrieve feed for an agent
feed = retriever.get_feed(interests=["crypto", "technology"], mode="preference")
```

### Mode switching

```python
# Same retriever, different modes
preference_feed = retriever.get_feed(interests=["crypto"], mode="preference")
random_feed = retriever.get_feed(mode="random")
```

### Integration with SocialAgent

```python
from prism.rag.formatting import format_feed_for_prompt
from prism.agents.social_agent import SocialAgent

# Get feed
posts = retriever.get_feed(interests=agent.interests)
feed_text = format_feed_for_prompt(posts)

# Agent decides
decision = await agent.decide(feed_text)
```
