# Plan: X Algorithm Ranking

## Summary

This feature adds X-algorithm-style feed ranking to PRISM by layering heuristic rescoring on top of the existing RAG retrieval. It implements candidate sourcing (in-network vs out-of-network), documented scale factors from X's algorithm, and author diversity controls. The ranker integrates as a wrapper around `FeedRetriever` and plugs into the simulation via an updated executor.

## Architecture

```
                         ┌─────────────────────────────────────────┐
                         │            XAlgorithmRanker             │
                         │                                          │
  agent.interests ──────►│  ┌────────────────┐  ┌────────────────┐ │
  agent.following ──────►│  │  In-Network    │  │ Out-of-Network │ │
                         │  │  Sourcing      │  │   Sourcing     │ │
                         │  │  (author_id    │  │   (RAG query)  │ │
                         │  │   in following)│  │                │ │
                         │  └───────┬────────┘  └───────┬────────┘ │
                         │          │                   │          │
                         │          └─────────┬─────────┘          │
                         │                    ▼                    │
                         │          ┌─────────────────┐            │
                         │          │  Merge & Score  │            │
                         │          │  (base = sim)   │            │
                         │          └────────┬────────┘            │
                         │                   │                     │
                         │                   ▼                     │
                         │          ┌─────────────────┐            │
                         │          │   Heuristic     │            │
                         │          │   Rescoring     │            │
                         │          │  - OON: 0.75x   │            │
                         │          │  - Reply: 0.75x │            │
                         │          │  - Author div   │            │
                         │          └────────┬────────┘            │
                         │                   │                     │
                         │                   ▼                     │
                         │          ┌─────────────────┐            │
                         │          │   Sort & Limit  │            │
                         │          │   (feed_size)   │            │
                         │          └────────┬────────┘            │
                         │                   │                     │
                         └───────────────────┼─────────────────────┘
                                             │
                                             ▼
                                        list[Post]
```

## Detailed Architecture

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `RankingConfig` | Config model with scale factors | `RAGConfig`, YAML loader |
| `SocialGraph` | Protocol for follow relationships | `SimulationState`, agents |
| `XAlgorithmRanker` | Main ranking pipeline | `FeedRetriever`, `SocialGraph` |
| `RankedCandidate` | Internal model with scoring metadata | `XAlgorithmRanker` |
| `RankingFeedExecutor` | Executor for simulation pipeline | `FeedRetrievalExecutor` |

### Data Flow: Feed Generation

```
┌─────────────┐
│   Agent     │
│ - interests │
│ - following │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                    XAlgorithmRanker                       │
│                                                          │
│  1. Get in-network candidates                            │
│     → Query ChromaDB by author_id in following           │
│     → Return posts with distances                        │
│                                                          │
│  2. Get out-of-network candidates                        │
│     → Query ChromaDB by interests embedding              │
│     → Exclude authors in following                       │
│     → Return posts with distances                        │
│                                                          │
│  3. Convert distances to similarity scores               │
│     → similarity = 1 - (distance / 2)                    │
│                                                          │
│  4. Apply scale factors                                  │
│     → OON: score *= 0.75                                 │
│     → Reply: score *= 0.75 (if parent_id set)            │
│                                                          │
│  5. Apply author diversity                               │
│     → Track author occurrences                           │
│     → score *= max(floor, decay^occurrence)              │
│                                                          │
│  6. Sort by final score, take top N                      │
└──────────────────────────────────────────────────────────┘
       │
       ▼
  list[Post]
```

## File Structure

```
prism/
├── rag/
│   ├── config.py           # MODIFY: Add RankingConfig
│   ├── models.py           # MODIFY: Add parent_id to Post
│   ├── retriever.py        # MODIFY: Add method to get with distances
│   └── ranker.py           # NEW: XAlgorithmRanker class
├── agents/
│   └── social_agent.py     # MODIFY: Add following field
├── simulation/
│   ├── state.py            # MODIFY: Add social graph access
│   ├── protocols.py        # MODIFY: Add SocialGraph protocol
│   └── executors/
│       └── feed.py         # MODIFY: Support ranking mode
configs/
└── default.yaml            # MODIFY: Add ranking section
```

## Critical: ChromaDB Distance Access

**Problem**: `FeedRetriever` returns `Post` objects, not similarity scores. The ranker needs base scores for heuristic rescoring.

**Solution**: Add a method to `FeedRetriever` that returns results with distances:

```python
def query_with_scores(
    self,
    query_text: str,
    n_results: int,
    where: dict | None = None,
) -> list[tuple[Post, float]]:
    """Query and return posts with similarity scores."""
    results = self._collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
        where=where,
    )
    # distances is cosine distance [0, 2], convert to similarity
    posts = self._results_to_posts(results)
    distances = results["distances"][0]
    similarities = [1 - (d / 2) for d in distances]
    return list(zip(posts, similarities))
```

## Implementation Phases

1. **Phase 1: Data Model** - Add `parent_id` to Post, `following` to SocialAgent
2. **Phase 2: Configuration** - Create `RankingConfig`, integrate with YAML
3. **Phase 3: Social Graph** - Define protocol, simple implementation
4. **Phase 4: Ranker Core** - Implement `XAlgorithmRanker` with scale factors
5. **Phase 5: Integration** - Update executor, wire into simulation

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Ranker wraps retriever | Composition | Keeps RAG retrieval reusable, ranker adds layer |
| Scale factors in config | Pydantic model | Matches existing config pattern, validated |
| Simple social graph | Protocol + dict | Minimal complexity, can evolve later |
| Distance → similarity | `1 - (d/2)` | ChromaDB cosine distance [0,2] to similarity [0,1] |
| Author tracking per-call | Instance state | Reset each feed generation, no persistence needed |

## Configuration Example

```yaml
rag:
  collection_name: posts
  embedding_model: all-MiniLM-L6-v2
  feed_size: 10
  mode: preference  # Backward compatible default

ranking:
  mode: x_algo  # x_algo | preference | random
  out_of_network_scale: 0.75
  reply_scale: 0.75
  author_diversity_decay: 0.5
  author_diversity_floor: 0.25
  in_network_limit: 50
  out_of_network_limit: 50
```

## Files to Modify

| File | Change |
|------|--------|
| `prism/rag/config.py` | Add `RankingConfig` class |
| `prism/rag/models.py` | Add `parent_id: str \| None` field to Post |
| `prism/rag/retriever.py` | Add `query_with_scores()` method |
| `prism/agents/social_agent.py` | Add `following: set[str]` field |
| `prism/simulation/protocols.py` | Add `SocialGraphProtocol` |
| `prism/simulation/state.py` | Add social graph accessor |
| `prism/simulation/executors/feed.py` | Use ranker when mode=x_algo |
| `configs/default.yaml` | Add `ranking:` section |

## New Files

| File | Purpose |
|------|---------|
| `prism/rag/ranker.py` | `XAlgorithmRanker` class with ranking pipeline |
| `tests/rag/test_ranker.py` | Unit tests for ranker |

## Verification

1. **Unit tests**: Scale factors, author diversity, candidate mixing
2. **Integration test**: 10 agents with follows, verify INN/OON split
3. **Spec tests**: LLM verification of code structure

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ChromaDB `where` clause complexity | Test filtering by author_id early |
| Score normalization edge cases | Handle zero distances (exact match) |
| Empty following set | Treat all as OON, valid degradation |
| Performance with many follows | Batch author queries if needed |

## Limitations (MVP)

1. **No engagement velocity** - Static post metrics only
2. **No user feedback** - No "show more"/"show less" signals
3. **No source diversity** - Only author diversity implemented
4. **Simple social graph** - No edge weights or relationship strength

## References

- [X Algorithm Research](../../../aidocs/x-algorithm-research.md)
- [Feature 002: RAG Feed System](../_completed/002-rag-feed-system/)
- [X Algorithm GitHub](https://github.com/twitter/the-algorithm)
