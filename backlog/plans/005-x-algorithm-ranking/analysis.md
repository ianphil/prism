# X Algorithm Ranking Analysis

## Executive Summary

This feature ports key elements from X's open-sourced recommendation algorithm to enable realistic feed curation. The implementation layers ranking on top of the existing `FeedRetriever`, adding candidate sourcing (in-network vs out-of-network) and documented heuristic scale factors.

| Pattern | Integration Point |
|---------|-------------------|
| RAG retrieval | `FeedRetriever.get_feed()` provides base similarity scores |
| Configuration hierarchy | `RAGConfig` extended with `RankingConfig` |
| Executor pattern | `FeedRetrievalExecutor` enhanced to use ranker |
| Pydantic models | New `RankedCandidate` model follows existing patterns |

## Architecture Comparison

### Current Architecture

```
┌─────────────┐       ┌────────────────┐       ┌────────────┐
│ SocialAgent │──────►│ FeedRetriever  │──────►│  ChromaDB  │
│ (interests) │       │ (preference/   │       │ (vectors)  │
└─────────────┘       │  random mode)  │       └────────────┘
                      └───────┬────────┘
                              │
                              ▼
                         list[Post]
```

The current system retrieves posts based on:
1. **Preference mode**: Embedding similarity to agent interests
2. **Random mode**: Uniform random sampling

No distinction between in-network (followed) and out-of-network (discovered) content.

### Target Architecture

```
┌─────────────┐       ┌───────────────┐       ┌───────────────┐
│ SocialAgent │──────►│ XAlgorithm    │──────►│ FeedRetriever │
│ + following │       │ Ranker        │       │ (base scores) │
└─────────────┘       └───────┬───────┘       └───────────────┘
                              │
                      ┌───────┴───────┐
                      │               │
               ┌──────▼──────┐ ┌──────▼──────┐
               │ In-Network  │ │Out-of-Net   │
               │ Candidates  │ │ Candidates  │
               └──────┬──────┘ └──────┬──────┘
                      │               │
                      └───────┬───────┘
                              ▼
                      ┌───────────────┐
                      │ Heuristic     │
                      │ Rescoring     │
                      │ - OON scale   │
                      │ - Reply scale │
                      │ - Author div  │
                      └───────┬───────┘
                              ▼
                         list[Post]
```

## Pattern Mapping

### 1. Configuration Pattern

**Current Implementation:**
```python
# prism/rag/config.py
class RAGConfig(BaseModel):
    mode: Literal["preference", "random"] = "preference"
    feed_size: int = Field(default=5, ge=1, le=20)
```

**Target Evolution:**
```python
# prism/rag/config.py (extended)
class RankingConfig(BaseModel):
    mode: Literal["x_algo", "preference", "random"] = "preference"
    out_of_network_scale: float = 0.75
    reply_scale: float = 0.75
    author_diversity_decay: float = 0.5
    author_diversity_floor: float = 0.25
    in_network_limit: int = 50
    out_of_network_limit: int = 50
```

### 2. Retriever Pattern

**Current Implementation:**
```python
# prism/rag/retriever.py
class FeedRetriever:
    def get_feed(self, interests: list[str] | None = None,
                 mode: Literal["preference", "random"] | None = None) -> list[Post]:
```

**Target Evolution:**
Wrap `FeedRetriever` in an `XAlgorithmRanker` that:
1. Gets candidates from both in-network and out-of-network sources
2. Computes base scores using similarity
3. Applies heuristic rescoring
4. Returns ranked feed

### 3. Social Graph (New)

**Currently Missing:** No social graph exists for follow relationships.

**Required:**
```python
class SocialGraph(Protocol):
    def get_following(self, agent_id: str) -> set[str]: ...
    def is_following(self, follower_id: str, followee_id: str) -> bool: ...
```

This is a prerequisite dependency. The simplest implementation:
- Store follow edges in `SimulationState` or a dedicated graph structure
- `SocialAgent` needs a `following: set[str]` field

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| `FeedRetriever` | ✅ | Core RAG retrieval with preference/random modes |
| `RAGConfig` | ✅ | Configuration model with validation |
| `Post` model | ✅ | Has `author_id`, `likes`, `reshares`, `replies` |
| `FeedRetrievalExecutor` | ✅ | Executor pattern for simulation pipeline |
| `SimulationState` | ✅ | Central state with agents and posts |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| `RankingConfig` | ❌ | New Pydantic model with scale factors |
| `SocialGraph` | ❌ | Protocol + simple implementation |
| `XAlgorithmRanker` | ❌ | Main ranking logic |
| `RankedCandidate` | ❌ | Internal model with scoring metadata |
| Agent `following` field | ❌ | Extend `SocialAgent` |

## Key Insights

### What Works Well

1. **Existing retriever is composable** - Can be used as the base score provider for the ranker
2. **Post model has needed fields** - `author_id` for diversity, `is_reply` can be inferred
3. **Pydantic patterns established** - Config, model, validation patterns are consistent
4. **Executor pattern supports extension** - `FeedRetrievalExecutor` can be swapped for a ranking executor

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| No social graph | Add `following: set[str]` to `SocialAgent`, create `SocialGraph` protocol |
| No reply detection | Add `parent_id: str | None` field to `Post` for reply chains |
| ChromaDB returns Post, not scores | Query with `include=["distances"]` for similarity scores |
| Author diversity needs tracking | Ranker maintains occurrence count during feed generation |

### Design Considerations

1. **Where does ranking config live?**
   - Option A: Extend `RAGConfig` with ranking fields
   - Option B: Separate `RankingConfig` composed into `RAGConfig`
   - **Recommendation**: Option B - cleaner separation, ranking is optional

2. **How to handle missing social graph?**
   - If no `following` set, treat all candidates as out-of-network (OON)
   - Enables gradual adoption

3. **Score normalization?**
   - ChromaDB distances are cosine (0-2, lower is better)
   - Convert to similarity: `similarity = 1 - (distance / 2)`
   - Apply scale factors multiplicatively to similarity
