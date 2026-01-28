---
title: "X Algorithm Ranking Integration"
status: open
priority: medium
created: 2026-01-27
depends_on: ["20260127-rag-feed-system.md"]
---

# X Algorithm Ranking Integration

## Summary

Port key elements from X's open-sourced recommendation algorithm to enable realistic feed curation, including candidate sourcing, engagement-based ranking, and media boost heuristics.

## Motivation

The PRD's core hypothesis testing requires comparing algorithmic feeds vs random feeds. X's documented ranking heuristics (velocity boost, media multiplier, in-network preference) create the feedback loops that drive real-world virality. This enables controlled experiments on algorithm impact.

## Proposal

### Goals

- Implement candidate sourcing: in-network (followed) + out-of-network (embedding similarity)
- Port ranking score calculation with engagement signals
- Add media boost multiplier per PRD spec (2x-10x for posts with images/video)
- Make ranking configurable: full X mode, simplified preference, random, or custom hybrids
- Integrate with existing `FeedRetriever` as an optional ranking layer

### Non-Goals

- Full production-grade recommendation system
- ML-based engagement prediction (use heuristics only)
- Real-time algorithm updates based on X repo changes

## Design

Per PRD §4.5, the ranking system layers on top of RAG retrieval:

1. **Candidate Sourcing**
   - In-network: Posts from agents the current agent follows
   - Out-of-network: High-similarity posts from broader pool
2. **Ranking Score**: `base_score * velocity_boost * media_boost`
   - `base_score`: Embedding similarity to agent interests
   - `velocity_boost`: Engagement rate over time window
   - `media_boost`: Multiplier for posts with media flags
3. **Configuration**: YAML-driven mode selection and tunable weights
4. **Integration**: `XAlgorithmRanker` wraps `FeedRetriever`, reorders candidates

## Tasks

- [ ] Define `RankingConfig` with mode and weight parameters
- [ ] Implement candidate sourcing (in-network + out-of-network split)
- [ ] Implement `calculate_ranking_score()` with velocity and media boosts
- [ ] Create `XAlgorithmRanker` class wrapping feed retrieval
- [ ] Add ranking mode to simulation config (`x_algo`, `preference`, `random`)
- [ ] Write tests: score calculation, candidate mixing, mode switching
