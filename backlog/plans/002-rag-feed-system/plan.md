# Plan: RAG Feed System with ChromaDB

## Summary

Implement a RAG-based feed retrieval system using ChromaDB as the vector store. Posts are embedded and indexed, then retrieved based on agent interests (preference mode) or uniformly sampled (random mode). The system integrates with the existing `SocialAgent` by providing formatted feed text with media indicators and engagement stats.

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                       RAG Feed System                                  │
│                                                                        │
│  configs/default.yaml                                                  │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────────┐                                                   │
│  │ PrismConfig     │                                                   │
│  │  ├── llm: ...   │                                                   │
│  │  └── rag: RAGConfig                                                 │
│  │       ├── collection_name                                           │
│  │       ├── embedding_model                                           │
│  │       ├── persist_directory                                         │
│  │       ├── feed_size                                                 │
│  │       └── mode                                                      │
│  └────────┬────────┘                                                   │
│           │                                                            │
│           ▼                                                            │
│  ┌────────────────────┐     ┌────────────────────┐                     │
│  │  ChromaDB Client   │────▶│    Collection      │                     │
│  │  (in-memory or     │     │  "posts"           │                     │
│  │   persistent)      │     │  + EmbeddingFunc   │                     │
│  └────────────────────┘     └─────────┬──────────┘                     │
│                                       │                                │
│                                       ▼                                │
│  ┌────────────────────────────────────────────────────────┐            │
│  │                    FeedRetriever                        │            │
│  │                                                         │            │
│  │  add_post(post) ─────────▶ embed + upsert to collection │            │
│  │  add_posts(posts) ───────▶ batch embed + upsert        │            │
│  │                                                         │            │
│  │  get_feed(interests, mode)                              │            │
│  │    ├── "preference" ──▶ query by interest embedding     │            │
│  │    └── "random" ──────▶ sample from all post IDs        │            │
│  │                                                         │            │
│  │  ──────────────────▶ list[Post]                         │            │
│  └────────────────────────────────────────────────────────┘            │
│                                       │                                │
│                                       ▼                                │
│  ┌────────────────────┐                                                │
│  │  format_feed()     │ ──▶ Formatted text with media + stats          │
│  └────────────────────┘                                                │
│           │                                                            │
│           ▼                                                            │
│  SocialAgent.decide(formatted_feed) ──▶ AgentDecision                  │
└───────────────────────────────────────────────────────────────────────┘
```

## Detailed Architecture

```
Post Creation Flow:
───────────────────
Post(id, author_id, text, timestamp, has_media, ..., likes, reshares, replies, velocity)
    │
    ▼
FeedRetriever.add_post(post)
    │
    ├── Embed post.text via EmbeddingFunction
    │
    └── collection.upsert(
            ids=[post.id],
            documents=[post.text],
            metadatas=[{author_id, timestamp, has_media, ...}]
        )


Feed Retrieval Flow (Preference Mode):
──────────────────────────────────────
agent_interests = ["crypto", "technology", "startups"]
    │
    ▼
FeedRetriever.get_feed(interests=agent_interests, mode="preference")
    │
    ├── query_text = " ".join(interests)  # "crypto technology startups"
    │
    ├── collection.query(query_texts=[query_text], n_results=feed_size)
    │
    └── return [Post.from_chroma_result(...) for result in results]


Feed Retrieval Flow (Random Mode):
──────────────────────────────────
FeedRetriever.get_feed(interests=None, mode="random")
    │
    ├── all_ids = collection.get()["ids"]
    │
    ├── sampled_ids = random.sample(all_ids, min(feed_size, len(all_ids)))
    │
    ├── results = collection.get(ids=sampled_ids, include=["documents", "metadatas"])
    │
    └── return [Post.from_chroma_result(...) for result in results]


Feed Rendering:
───────────────
posts: list[Post]
    │
    ▼
format_feed_for_prompt(posts)
    │
    └── For each post:
        """
        Post #1:
        "Just mass adoption starting? My local coffee shop now accepts Bitcoin!"
        [📷 IMAGE: Photo of a coffee shop counter with a Bitcoin payment terminal]
        ❤️ 89 | 🔁 34 | 💬 12 | 3h ago
        """
```

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `Post` | Data model for social media posts | Pydantic, ChromaDB metadata |
| `RAGConfig` | Configuration for RAG system | PrismConfig, YAML loading |
| `create_collection()` | Factory for ChromaDB collection | RAGConfig, embedding functions |
| `FeedRetriever` | Core retrieval logic | ChromaDB collection, Post model |
| `format_feed_for_prompt()` | Renders posts for agent prompts | Post list, SocialAgent |
| `OllamaEmbeddingFunction` | Custom embedding via Ollama | Ollama API (optional) |

### Data Flow: Agent Receives Feed

```
1. Load config ──── configs/default.yaml ──▶ PrismConfig (with RAGConfig)
2. Create collection ─ RAGConfig ──▶ ChromaDB Collection
3. Create retriever ── Collection ──▶ FeedRetriever
4. Index posts ─────── FeedRetriever.add_posts(seed_posts)
5. Get feed ────────── FeedRetriever.get_feed(
                           interests=agent.interests,
                           mode=config.rag.mode
                       ) ──▶ list[Post]
6. Format feed ─────── format_feed_for_prompt(posts) ──▶ str
7. Agent decides ───── SocialAgent.decide(feed_text) ──▶ AgentDecision
```

## File Structure

```
prism/
├── __init__.py
├── llm/
│   ├── config.py                 # MODIFY: add RAGConfig to PrismConfig
│   └── ...
├── rag/
│   ├── __init__.py               # NEW: exports
│   ├── models.py                 # NEW: Post dataclass
│   ├── config.py                 # NEW: RAGConfig model
│   ├── embeddings.py             # NEW: OllamaEmbeddingFunction (optional)
│   ├── store.py                  # NEW: create_collection() factory
│   ├── retriever.py              # NEW: FeedRetriever class
│   └── formatting.py             # NEW: format_feed_for_prompt()
configs/
├── default.yaml                  # MODIFY: add rag section
tests/
├── rag/
│   ├── __init__.py               # NEW
│   ├── test_models.py            # NEW: Post model tests
│   ├── test_config.py            # NEW: RAGConfig tests
│   ├── test_store.py             # NEW: collection creation tests
│   ├── test_retriever.py         # NEW: retrieval tests
│   ├── test_formatting.py        # NEW: feed rendering tests
│   └── test_integration.py       # NEW: end-to-end tests
```

## Critical: Random Sampling

**Problem**: ChromaDB doesn't have native random sampling. We need to support random mode for experiment control groups.

**Solution**:
```python
def get_feed(self, interests: list[str] | None = None, mode: str = "preference") -> list[Post]:
    if mode == "random":
        # Get all document IDs
        all_data = self._collection.get()
        all_ids = all_data["ids"]

        # Sample randomly
        sample_size = min(self._feed_size, len(all_ids))
        sampled_ids = random.sample(all_ids, sample_size)

        # Retrieve sampled posts
        results = self._collection.get(
            ids=sampled_ids,
            include=["documents", "metadatas"]
        )
        return self._results_to_posts(results)
    else:
        # Preference mode: query by interests
        ...
```

**Performance Note**: This approach loads all IDs into memory. Acceptable for corpora < 100K posts. Document this limitation.

## Implementation Phases

### Phase 1: Data Model and Configuration
- `Post` Pydantic model with all PRD-specified fields
- `RAGConfig` model with collection, embedding, retrieval settings
- Extend `PrismConfig` with `rag` section
- Update `configs/default.yaml`

### Phase 2: ChromaDB Integration
- `create_collection()` factory function
- Embedding function setup (sentence-transformers default)
- Optional `OllamaEmbeddingFunction` for Ollama-only users

### Phase 3: Feed Retrieval
- `FeedRetriever` class with `add_post()`, `add_posts()`, `get_feed()`
- Preference mode: query by agent interests embedding
- Random mode: sample from all post IDs

### Phase 4: Feed Rendering
- `format_feed_for_prompt()` function
- Media indicators (📷, 🎬, 🎞️)
- Engagement stats (❤️, 🔁, 💬)
- Relative timestamps

### Phase 5: Integration
- End-to-end test: index posts → retrieve feed → format → agent decides
- Integration with existing SocialAgent

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector store | ChromaDB | Lightweight, Python-native, PRD-specified |
| Default embeddings | sentence-transformers | Fast batch embedding, no external deps |
| Ollama embeddings | Optional via config | Consistency with Ollama-first users |
| Default model | `all-MiniLM-L6-v2` | Fast, good quality, widely used |
| Random sampling | Python-side | ChromaDB limitation; acceptable for MVP |
| Timestamp storage | ISO 8601 string | Human-readable, ChromaDB-compatible |
| Persistence | Config-driven | `null` = in-memory, path = persistent |
| Feed size | Configurable 1-20 | PRD specifies 5-10; allow experimentation |

## Configuration Example

```yaml
# configs/default.yaml
llm:
  provider: ollama
  host: "http://localhost:11434"
  model_id: mistral
  temperature: 0.7
  max_tokens: 512
  seed: null

rag:
  collection_name: posts           # ChromaDB collection name
  embedding_model: all-MiniLM-L6-v2  # sentence-transformers model
  embedding_provider: sentence-transformers  # or "ollama"
  persist_directory: null          # null = in-memory, path = persistent
  feed_size: 5                     # posts per agent feed (1-20)
  mode: preference                 # "preference" or "random"
```

## Files to Modify

| File | Change |
|------|--------|
| `prism/llm/config.py` | Import and add `RAGConfig` to `PrismConfig` |
| `configs/default.yaml` | Add `rag:` section with default values |

## New Files

| File | Purpose |
|------|---------|
| `prism/rag/__init__.py` | Package exports |
| `prism/rag/models.py` | `Post` Pydantic model |
| `prism/rag/config.py` | `RAGConfig` Pydantic model |
| `prism/rag/embeddings.py` | `OllamaEmbeddingFunction` class |
| `prism/rag/store.py` | `create_collection()` factory |
| `prism/rag/retriever.py` | `FeedRetriever` class |
| `prism/rag/formatting.py` | `format_feed_for_prompt()` function |
| `tests/rag/__init__.py` | Test package |
| `tests/rag/test_models.py` | Post model tests |
| `tests/rag/test_config.py` | RAGConfig tests |
| `tests/rag/test_store.py` | Collection creation tests |
| `tests/rag/test_retriever.py` | Retrieval tests |
| `tests/rag/test_formatting.py` | Feed rendering tests |
| `tests/rag/test_integration.py` | End-to-end tests |

## Verification

1. `uv run pytest tests/rag/` — all RAG tests pass
2. `uv run ruff check . && uv run flake8 . && uv run black --check .` — linting clean
3. Integration test: index 100 posts → retrieve feed → verify relevance
4. Mode switching: same corpus, different modes produce different feeds

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ChromaDB API changes | Pin version; abstract behind FeedRetriever |
| Embedding model unavailable | sentence-transformers is pip-installable; Ollama optional |
| Poor retrieval quality | Test with curated posts; tune embedding model if needed |
| Memory pressure (large corpus) | Document limits; support persistent storage |
| Random sampling slow | Document O(n) for get-all-IDs; acceptable for MVP |

## Limitations (MVP)

1. **No time decay** — All posts weighted equally regardless of age. Future: weight by recency.
2. **No agent exclusions** — Agent may see same post twice. Future: track seen posts.
3. **No concurrent access** — Single-threaded indexing/retrieval. Future: async ChromaDB client.
4. **No hybrid mode** — Preference OR random, not both. Future: blend with configurable ratio.
5. **Single embedding model** — One model per collection. Future: support model switching.

## References

- [ChromaDB Python Docs](https://docs.trychroma.com/getting-started)
- [ChromaDB Embedding Functions](https://docs.trychroma.com/guides/embeddings)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama Embeddings API](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings)
- [PRD §4.4: Memory and RAG System](../../../aidocs/prd.md)
