# Data Model: X Algorithm Ranking

## Entities

### RankingConfig

Configuration for the X algorithm ranking system.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| mode | Literal["x_algo", "preference", "random"] | No | "preference" | Ranking mode selection |
| out_of_network_scale | float | No | 0.75 | Scale factor for OON posts (0.0-1.0) |
| reply_scale | float | No | 0.75 | Scale factor for replies (0.0-1.0) |
| author_diversity_decay | float | No | 0.5 | Decay per author occurrence (0.0-1.0) |
| author_diversity_floor | float | No | 0.25 | Minimum score after decay (0.0-1.0) |
| in_network_limit | int | No | 50 | Max in-network candidates (1-500) |
| out_of_network_limit | int | No | 50 | Max out-of-network candidates (1-500) |

**Relationships:**
- Composed into `RAGConfig` as optional field
- Read by `XAlgorithmRanker`

**Invariants:**
- All scale factors must be in range [0.0, 1.0]
- `author_diversity_floor` must be <= `author_diversity_decay`
- Limits must be >= 1

### RankedCandidate

Internal model for candidates during ranking pipeline.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| post | Post | Yes | - | The post being ranked |
| base_score | float | Yes | - | Similarity score from embedding (0.0-1.0) |
| is_in_network | bool | Yes | - | True if author in agent's following |
| is_reply | bool | Yes | - | True if post.parent_id is set |
| author_occurrence | int | Yes | 0 | Count of this author in current ranking |
| final_score | float | No | None | Score after heuristic rescoring |

**Relationships:**
- Contains one `Post`
- Created by `XAlgorithmRanker` during ranking

**Invariants:**
- `base_score` in [0.0, 1.0]
- `author_occurrence` >= 0
- `final_score` calculated only after rescoring

### Post (Extended)

Add reply chain support to existing Post model.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| parent_id | str \| None | No | None | ID of parent post if this is a reply |

**Relationships:**
- Self-referential: reply → parent Post

**Invariants:**
- If `parent_id` is set, post is a reply
- Parent may or may not exist in current posts list

### SocialAgent (Extended)

Add following set to existing SocialAgent.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| following | set[str] | No | set() | Agent IDs this agent follows |

**Relationships:**
- References other `SocialAgent` by ID
- Used by `XAlgorithmRanker` for INN/OON classification

**Invariants:**
- Cannot follow self (agent_id not in following)
- All IDs in following should exist in simulation

## State Transitions

### RankedCandidate Lifecycle

```
           ┌─────────────┐
           │   Created   │
           │ (base_score │
           │  computed)  │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │ Classified  │
           │ (INN/OON    │
           │  tagged)    │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │  Rescored   │
           │ (scale      │
           │  factors    │
           │  applied)   │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │   Sorted    │
           │ (by final   │
           │  score)     │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │  Selected   │
           │ (top N for  │
           │  feed)      │
           └─────────────┘
```

| State | Description |
|-------|-------------|
| Created | Post retrieved with base similarity score |
| Classified | Tagged as in-network or out-of-network |
| Rescored | All scale factors applied (OON, reply, author diversity) |
| Sorted | Candidates ordered by final score descending |
| Selected | Top feed_size candidates selected for feed |

### Ranking Mode Selection

```
      ┌──────────────────────────────────────────┐
      │           ranking.mode config            │
      └──────────────────┬───────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌──────────┐     ┌─────────┐
   │  x_algo │     │preference│     │ random  │
   │         │     │          │     │         │
   │ INN/OON │     │ Similarity│    │ Uniform │
   │ + scale │     │   only   │     │ sample  │
   │ factors │     │          │     │         │
   └─────────┘     └──────────┘     └─────────┘
```

## Data Flow

### Feed Generation (x_algo mode)

```
┌─────────────────────────────────────────────────────────────────┐
│ XAlgorithmRanker.get_feed(agent)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Get in-network candidates                                   │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ChromaDB.query(                                      │    │
│     │   where={"author_id": {"$in": list(agent.following)}}│    │
│     │   include=["documents", "metadatas", "distances"]    │    │
│     │ )                                                    │    │
│     └──────────────────────────┬──────────────────────────┘    │
│                                │                               │
│  2. Get out-of-network candidates                              │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ChromaDB.query(                                      │    │
│     │   query_texts=[" ".join(agent.interests)]            │    │
│     │   where={"author_id": {"$nin": list(agent.following)}}│   │
│     │   include=["documents", "metadatas", "distances"]    │    │
│     │ )                                                    │    │
│     └──────────────────────────┬──────────────────────────┘    │
│                                │                               │
│  3. Create RankedCandidates                                    │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ for post, distance in results:                       │    │
│     │   similarity = 1 - (distance / 2)                    │    │
│     │   RankedCandidate(                                   │    │
│     │     post=post,                                       │    │
│     │     base_score=similarity,                           │    │
│     │     is_in_network=author_id in following,            │    │
│     │     is_reply=post.parent_id is not None,             │    │
│     │   )                                                  │    │
│     └──────────────────────────┬──────────────────────────┘    │
│                                │                               │
│  4. Apply heuristic rescoring                                  │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ author_counts = {}                                   │    │
│     │ for candidate in candidates:                         │    │
│     │   score = candidate.base_score                       │    │
│     │   if not candidate.is_in_network:                    │    │
│     │     score *= config.out_of_network_scale             │    │
│     │   if candidate.is_reply:                             │    │
│     │     score *= config.reply_scale                      │    │
│     │   occurrence = author_counts.get(author_id, 0)       │    │
│     │   if occurrence > 0:                                 │    │
│     │     decay = max(floor, decay_factor ** occurrence)   │    │
│     │     score *= decay                                   │    │
│     │   author_counts[author_id] = occurrence + 1          │    │
│     │   candidate.final_score = score                      │    │
│     └──────────────────────────┬──────────────────────────┘    │
│                                │                               │
│  5. Sort and return top N                                      │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ sorted_candidates = sorted(                          │    │
│     │   candidates,                                        │    │
│     │   key=lambda c: c.final_score,                       │    │
│     │   reverse=True                                       │    │
│     │ )                                                    │    │
│     │ return [c.post for c in sorted_candidates[:feed_size]]│   │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| RankingConfig | out_of_network_scale in [0.0, 1.0] | ValidationError |
| RankingConfig | reply_scale in [0.0, 1.0] | ValidationError |
| RankingConfig | author_diversity_decay in [0.0, 1.0] | ValidationError |
| RankingConfig | author_diversity_floor in [0.0, 1.0] | ValidationError |
| RankingConfig | author_diversity_floor <= author_diversity_decay | ValidationError |
| RankingConfig | in_network_limit >= 1 | ValidationError |
| RankingConfig | out_of_network_limit >= 1 | ValidationError |
| RankedCandidate | base_score in [0.0, 1.0] | ValueError |
| SocialAgent | agent_id not in following | ValueError |
