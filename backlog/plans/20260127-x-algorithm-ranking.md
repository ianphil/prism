---
title: "X Algorithm Ranking Integration"
status: open
priority: medium
created: 2026-01-27
updated: 2026-01-31
depends_on: ["002-rag-feed-system"]
---

# X Algorithm Ranking Integration

## Summary

Port key elements from X's open-sourced recommendation algorithm to enable realistic feed curation, including candidate sourcing, heuristic rescoring factors, and author diversity controls.

## Motivation

The PRD's core hypothesis testing requires comparing algorithmic feeds vs random feeds. X's documented ranking heuristics create the feedback loops that drive real-world virality. This enables controlled experiments on algorithm impact.

## Research Findings

Based on analysis of X's open-sourced repo (see `aidocs/x-algorithm-research.md`):

1. **No explicit velocity/media boost multipliers** exist in the heuristic layer - those effects are learned by ML models through engagement features
2. **Documented scale factors** apply multiplicatively after ML scoring
3. **In-network preference** is implemented as a 0.75x penalty on out-of-network content
4. **Author diversity** uses exponential decay to prevent feed domination

## Proposal

### Goals

- Implement candidate sourcing: in-network (followed) + out-of-network (embedding similarity)
- Apply documented heuristic scale factors from X's actual algorithm
- Implement author diversity decay within feeds
- Make ranking configurable: x_algo, preference, random modes
- Integrate with existing `FeedRetriever` as a ranking layer

### Non-Goals

- Full production-grade recommendation system
- ML-based heavy ranker (use embedding similarity as base score)
- Invented boost multipliers not in the actual algorithm

### Prerequisites

- **Social network graph**: Requires follow relationships between agents to distinguish in-network vs out-of-network posts

## Design

### Architecture

```
Candidate Pool (all posts)
        │
        ▼
┌─────────────────────────┐
│   Candidate Sourcing    │
│  • In-network: followed │
│  • Out-of-network: RAG  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Base Score (RAG)      │
│  Embedding similarity   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Heuristic Rescoring    │
│  score *= scale_factors │
└───────────┬─────────────┘
            │
            ▼
      Ranked Feed
```

### Documented Scale Factors

From `ScoredTweetsParam.scala` and `RescoringFactorProvider.scala`:

| Factor | Default | Description |
|--------|---------|-------------|
| `out_of_network_scale` | 0.75 | OON posts scored at 75% |
| `reply_scale` | 0.75 | Replies scored at 75% |
| `author_diversity_decay` | 0.5 | Repeat author penalty per occurrence |
| `author_diversity_floor` | 0.25 | Minimum score after decay |

### Ranking Score Calculation

```python
def calculate_ranking_score(
    post: Post,
    agent: Agent,
    base_score: float,
    is_in_network: bool,
    author_occurrence: int,
    config: RankingConfig
) -> float:
    score = base_score

    # Out-of-network penalty
    if not is_in_network:
        score *= config.out_of_network_scale  # 0.75

    # Reply penalty
    if post.is_reply:
        score *= config.reply_scale  # 0.75

    # Author diversity decay
    if author_occurrence > 0:
        decay = max(
            config.author_diversity_floor,
            config.author_diversity_decay ** author_occurrence
        )
        score *= decay

    return score
```

### Candidate Sourcing

```python
def get_candidates(
    agent: Agent,
    social_graph: SocialGraph,
    post_store: PostStore,
    config: RankingConfig
) -> list[Post]:
    # In-network: posts from followed agents
    followed_ids = social_graph.get_following(agent.id)
    in_network = post_store.get_posts_by_authors(followed_ids)

    # Out-of-network: RAG similarity search
    out_of_network = post_store.similarity_search(
        query=agent.interests_embedding,
        exclude_authors=followed_ids,
        limit=config.oon_candidate_limit
    )

    return in_network + out_of_network
```

### Configuration

```yaml
ranking:
  mode: "x_algo"  # x_algo | preference | random

  # Scale factors (X algorithm defaults)
  out_of_network_scale: 0.75
  reply_scale: 0.75
  author_diversity_decay: 0.5
  author_diversity_floor: 0.25

  # Candidate limits
  in_network_limit: 50
  out_of_network_limit: 50
```

## Tasks

- [ ] Define `RankingConfig` dataclass with scale factor parameters
- [ ] Implement `SocialGraph` protocol for follow relationship queries
- [ ] Implement candidate sourcing (in-network + out-of-network split)
- [ ] Implement `calculate_ranking_score()` with documented scale factors
- [ ] Implement author diversity tracking within feed generation
- [ ] Create `XAlgorithmRanker` class wrapping feed retrieval
- [ ] Add ranking mode to simulation config
- [ ] Write tests: scale factor application, candidate mixing, author diversity decay
