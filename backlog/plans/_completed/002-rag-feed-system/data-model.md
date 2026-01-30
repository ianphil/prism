# Data Model: RAG Feed System

## Entities

### Post

A social media post that can be indexed in ChromaDB and retrieved for agent feeds.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | str | Yes | - | Unique identifier (e.g., UUID or "post_001") |
| author_id | str | Yes | - | ID of the agent/user who created the post |
| text | str | Yes | - | The post content (embedded for similarity search) |
| timestamp | datetime | Yes | - | When the post was created |
| has_media | bool | No | False | Whether the post contains visual media |
| media_type | str \| None | No | None | Type of media: "image", "video", "gif" |
| media_description | str \| None | No | None | Description of the media content |
| likes | int | No | 0 | Number of likes (engagement metric) |
| reshares | int | No | 0 | Number of reshares (engagement metric) |
| replies | int | No | 0 | Number of replies (engagement metric) |
| velocity | float | No | 0.0 | Engagement rate over time (for X algorithm) |

**Relationships:**
- References 1 author (author_id → Agent.id, resolved externally)
- May have 0-N replies (tracked as separate Posts with parent reference — future)

**Invariants:**
- `id` must be unique within a collection
- `text` must be non-empty
- `media_type` must be one of: None, "image", "video", "gif"
- `media_description` should only be set if `has_media` is True
- `likes`, `reshares`, `replies` must be non-negative
- `velocity` must be non-negative

**ChromaDB Mapping:**

| Post Field | ChromaDB Storage | Notes |
|------------|------------------|-------|
| id | `ids` | Primary key |
| text | `documents` | Embedded for similarity search |
| author_id | `metadatas["author_id"]` | String |
| timestamp | `metadatas["timestamp"]` | ISO 8601 string |
| has_media | `metadatas["has_media"]` | Boolean |
| media_type | `metadatas["media_type"]` | String or None |
| media_description | `metadatas["media_description"]` | String or None |
| likes | `metadatas["likes"]` | Integer |
| reshares | `metadatas["reshares"]` | Integer |
| replies | `metadatas["replies"]` | Integer |
| velocity | `metadatas["velocity"]` | Float |

### RAGConfig

Configuration for the RAG feed system.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| collection_name | str | No | "posts" | ChromaDB collection name |
| embedding_model | str | No | "all-MiniLM-L6-v2" | Embedding model name |
| embedding_provider | str | No | "sentence-transformers" | Provider: "sentence-transformers" or "ollama" |
| persist_directory | str \| None | No | None | Path for persistent storage; None = in-memory |
| feed_size | int | No | 5 | Number of posts per feed (1-20) |
| mode | str | No | "preference" | Retrieval mode: "preference" or "random" |

**Invariants:**
- `feed_size` must be between 1 and 20
- `mode` must be one of: "preference", "random"
- `embedding_provider` must be one of: "sentence-transformers", "ollama"
- If `embedding_provider` is "ollama", `embedding_model` should be a valid Ollama model

## State Transitions

### Post Lifecycle

```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │ add_post()
                           ▼
                    ┌─────────────┐
                    │   Indexed   │◀──────────────────┐
                    └──────┬──────┘                   │
                           │                          │
           ┌───────────────┼───────────────┐          │
           ▼               ▼               ▼          │
    ┌────────────┐  ┌────────────┐  ┌────────────┐   │
    │  Retrieved │  │   Liked    │  │  Reshared  │   │
    │  (in feed) │  │  (metrics  │  │  (metrics  │───┘
    └────────────┘  │  updated)  │  │  updated)  │  update_metrics()
                    └────────────┘  └────────────┘
```

| State | Description |
|-------|-------------|
| Created | Post object instantiated but not yet indexed |
| Indexed | Post embedded and stored in ChromaDB |
| Retrieved | Post included in an agent's feed |
| Liked/Reshared | Post metrics updated after agent engagement |

### Collection Lifecycle

```
    ┌─────────────────┐
    │   Not Created   │
    └────────┬────────┘
             │ create_collection()
             ▼
    ┌─────────────────┐
    │     Empty       │
    └────────┬────────┘
             │ add_post(s)
             ▼
    ┌─────────────────┐
    │    Populated    │◀───┐
    └────────┬────────┘    │
             │ get_feed()  │ add_post(s)
             ▼             │
    ┌─────────────────┐    │
    │   Queryable     │────┘
    └─────────────────┘
```

| State | Description |
|-------|-------------|
| Not Created | ChromaDB collection doesn't exist |
| Empty | Collection exists but has no posts |
| Populated | Collection has indexed posts |
| Queryable | Collection can return feeds (requires >= 1 post) |

## Data Flow

### Post Indexing

```
Post Object
    │
    ├── id ────────────────────────▶ collection.ids
    │
    ├── text ──┬───────────────────▶ EmbeddingFunction
    │          │                           │
    │          │                           ▼
    │          │                    embedding vector
    │          │                           │
    │          └───────────────────▶ collection.documents
    │
    └── (all other fields) ────────▶ collection.metadatas
                                           │
                                           ▼
                                    ChromaDB Collection
```

### Feed Retrieval (Preference Mode)

```
Agent Interests: ["crypto", "technology"]
    │
    ▼
query_text = "crypto technology"
    │
    ▼
EmbeddingFunction(query_text)
    │
    ▼
query_embedding
    │
    ▼
collection.query(query_embeddings=[...], n_results=feed_size)
    │
    ▼
ChromaDB Results: {ids, documents, metadatas, distances}
    │
    ▼
[Post.from_chroma_result(r) for r in results]
    │
    ▼
list[Post]
```

### Feed Retrieval (Random Mode)

```
collection.get()
    │
    ▼
all_ids: list[str]
    │
    ▼
random.sample(all_ids, feed_size)
    │
    ▼
sampled_ids: list[str]
    │
    ▼
collection.get(ids=sampled_ids, include=["documents", "metadatas"])
    │
    ▼
ChromaDB Results
    │
    ▼
[Post.from_chroma_result(r) for r in results]
    │
    ▼
list[Post]
```

### Feed Formatting

```
list[Post]
    │
    ▼
format_feed_for_prompt(posts)
    │
    ├── For each post:
    │   │
    │   ├── post.text ─────────────▶ "Just mass adoption..."
    │   │
    │   ├── post.has_media ────────▶ [📷 IMAGE: description]
    │   │   post.media_type            (if has_media)
    │   │   post.media_description
    │   │
    │   └── post.likes ────────────▶ ❤️ 89 | 🔁 34 | 💬 12 | 3h ago
    │       post.reshares
    │       post.replies
    │       post.timestamp
    │
    ▼
Formatted String (for SocialAgent.decide())
```

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| Post | id must be non-empty string | ValueError: id required |
| Post | text must be non-empty string | ValueError: text required |
| Post | media_type must be valid enum | ValueError: invalid media_type |
| Post | likes/reshares/replies must be >= 0 | ValueError: negative metric |
| Post | velocity must be >= 0 | ValueError: negative velocity |
| RAGConfig | feed_size must be 1-20 | ValueError: feed_size out of range |
| RAGConfig | mode must be "preference" or "random" | ValueError: invalid mode |
| RAGConfig | embedding_provider must be valid | ValueError: unknown provider |

## Example Data

### Post Instance

```python
Post(
    id="post_001",
    author_id="agent_42",
    text="Just mass adoption starting? My local coffee shop now accepts Bitcoin!",
    timestamp=datetime(2026, 1, 29, 10, 30, 0),
    has_media=True,
    media_type="image",
    media_description="Photo of a coffee shop counter with a Bitcoin payment terminal",
    likes=89,
    reshares=34,
    replies=12,
    velocity=2.5,
)
```

### ChromaDB Metadata

```python
{
    "author_id": "agent_42",
    "timestamp": "2026-01-29T10:30:00",
    "has_media": True,
    "media_type": "image",
    "media_description": "Photo of a coffee shop counter with a Bitcoin payment terminal",
    "likes": 89,
    "reshares": 34,
    "replies": 12,
    "velocity": 2.5,
}
```

### Formatted Feed Output

```
Post #1:
"Just mass adoption starting? My local coffee shop now accepts Bitcoin!"
[📷 IMAGE: Photo of a coffee shop counter with a Bitcoin payment terminal]
❤️ 89 | 🔁 34 | 💬 12 | 3h ago

Post #2:
"My local coffee shop now accepts Bitcoin payments. The future is here."
❤️ 23 | 🔁 8 | 💬 3 | 3h ago
```
