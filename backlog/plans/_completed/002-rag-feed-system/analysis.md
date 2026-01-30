# RAG Feed System Analysis

## Executive Summary

| Pattern | Integration Point |
|---------|-------------------|
| Pydantic models | `Post` dataclass follows `AgentDecision` pattern |
| Config-driven design | `RAGConfig` extends `PrismConfig` pattern |
| Async operations | `FeedRetriever` follows `SocialAgent.decide()` async pattern |
| Factory functions | `create_collection()` follows `create_llm_client()` pattern |
| Prompt formatting | Feed rendering extends `build_feed_prompt()` |

## Architecture Comparison

### Current Architecture

```
┌─────────────────────────────────────────────────────┐
│                  PRISM (Feature 001)                │
│                                                     │
│  configs/default.yaml ──▶ LLMConfig ──▶ OllamaChatClient
│                                              │      │
│                                              ▼      │
│  SocialAgent.decide(feed_text: str) ──▶ AgentDecision
│         │                                          │
│         └── feed_text is a raw string argument     │
└─────────────────────────────────────────────────────┘

Problem: Agents receive feed content as a hardcoded string.
         No mechanism for dynamic post retrieval or personalization.
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  PRISM (Feature 002)                             │
│                                                                  │
│  ChromaDB Collection                                             │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────┐                                                │
│  │   Posts     │  (embedded, indexed, with metadata)            │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────┐                                           │
│  │  FeedRetriever   │                                           │
│  │  • preference    │◀─── agent interests (embedding query)     │
│  │  • random        │◀─── uniform sampling                      │
│  └────────┬─────────┘                                           │
│           │ get_feed(agent_id, mode) → list[Post]               │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │  Feed Renderer   │  format_feed(posts) → str                 │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  SocialAgent.decide(formatted_feed) ──▶ AgentDecision           │
└─────────────────────────────────────────────────────────────────┘
```

## Pattern Mapping

### 1. Pydantic Data Models

**Current Implementation:**
```python
# prism/agents/decision.py
class AgentDecision(BaseModel):
    choice: Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
    reason: str
    content: str | None = None
```

**Target Evolution:**
```python
# prism/rag/models.py
class Post(BaseModel):
    id: str
    author_id: str
    text: str
    timestamp: datetime
    has_media: bool = False
    media_type: str | None = None  # "image", "video", "gif"
    media_description: str | None = None
    likes: int = 0
    reshares: int = 0
    replies: int = 0
    velocity: float = 0.0
```

Same pattern: Pydantic BaseModel with typed fields, defaults, and validation.

### 2. Configuration Pattern

**Current Implementation:**
```python
# prism/llm/config.py
class LLMConfig(BaseModel):
    host: str = "http://localhost:11434"
    model_id: str = "mistral"

class PrismConfig(BaseModel):
    llm: LLMConfig = LLMConfig()
```

**Target Evolution:**
```python
# prism/rag/config.py
class RAGConfig(BaseModel):
    collection_name: str = "posts"
    embedding_model: str = "nomic-embed-text"
    persist_directory: str | None = None  # None = in-memory
    feed_size: int = Field(default=5, ge=1, le=20)
    mode: Literal["preference", "random"] = "preference"

# Extends PrismConfig
class PrismConfig(BaseModel):
    llm: LLMConfig = LLMConfig()
    rag: RAGConfig = RAGConfig()  # NEW
```

### 3. Factory Functions

**Current Implementation:**
```python
# prism/llm/client.py
def create_llm_client(config: LLMConfig) -> OllamaChatClient:
    return OllamaChatClient(host=config.host, model_id=config.model_id)
```

**Target Evolution:**
```python
# prism/rag/store.py
def create_collection(config: RAGConfig) -> chromadb.Collection:
    client = chromadb.Client() if not config.persist_directory else ...
    return client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=...
    )
```

### 4. Async Operations

**Current Implementation:**
```python
# prism/agents/social_agent.py
async def decide(self, feed_text: str) -> AgentDecision:
    response = await self._agent.run(...)
    return AgentDecision(...)
```

**Target Evolution:**
```python
# prism/rag/retriever.py
async def get_feed(
    self,
    agent_interests: list[str] | None = None,
    mode: str = "preference"
) -> list[Post]:
    # Async interface for consistency, though ChromaDB is sync
    ...
```

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| `SocialAgent` | ✅ | Accepts feed_text as string |
| `AgentDecision` | ✅ | Structured output model |
| `build_feed_prompt()` | ✅ | Simple text formatting |
| `LLMConfig` / `PrismConfig` | ✅ | Config loading from YAML |
| `create_llm_client()` | ✅ | Factory for Ollama client |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| `Post` dataclass | ❌ | PRD §4.4, mirrors existing Pydantic pattern |
| `RAGConfig` | ❌ | Extends PrismConfig pattern |
| ChromaDB collection | ❌ | New dependency, factory function |
| Embedding function | ❌ | Ollama embeddings or sentence-transformers |
| `FeedRetriever` | ❌ | Core retrieval logic |
| Feed renderer | ❌ | Extends `build_feed_prompt()` pattern |

## Key Insights

### What Works Well

1. **Pydantic pattern** — `AgentDecision` demonstrates how to build validated models with constrained types. `Post` follows the same approach.

2. **Config-driven design** — `LLMConfig` + YAML loading is already established. Extending `PrismConfig` with `rag:` section is natural.

3. **Prompt template functions** — `build_feed_prompt()` already accepts text and formats it. New `format_feed_for_prompt()` extends this to render `Post` objects with media indicators.

4. **Async consistency** — `SocialAgent.decide()` is async. `FeedRetriever` can match this interface.

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| No existing embedding pipeline | Use ChromaDB's built-in embedding functions (Ollama or sentence-transformers) |
| No post storage | ChromaDB collection with metadata fields for filtering |
| Feed is static string | `FeedRetriever` dynamically retrieves posts and formats them |
| No agent profile storage | Agent interests passed to retriever; profile storage is future feature |
| ChromaDB is sync | Wrap in async-compatible interface (run_in_executor or sync wrapper) |

### Technical Considerations

1. **Embedding Model Choice**
   - **Option A**: `nomic-embed-text` via Ollama — consistent with Ollama-first approach
   - **Option B**: `sentence-transformers` — widely used, fast, no external deps
   - **Recommendation**: Support both via config; default to Ollama if available

2. **Persistence**
   - Development: In-memory ChromaDB (fast, no setup)
   - Production: Persistent directory (checkpointing, resume)
   - Config-driven: `persist_directory: null` vs path

3. **Feed Size**
   - PRD specifies 5-10 candidate posts per agent turn
   - Config parameter with bounds: `feed_size: int = Field(default=5, ge=1, le=20)`

4. **Media Simulation**
   - PRD defines `has_media`, `media_type`, `media_description` fields
   - Feed renderer formats these with visual indicators per PRD examples
