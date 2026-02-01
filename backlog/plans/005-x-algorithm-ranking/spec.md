# Specification: X Algorithm Ranking

## Overview

### Problem Statement

PRISM's core hypothesis testing requires comparing algorithmic feeds vs random feeds to study virality. Currently, `FeedRetriever` only supports preference-based (similarity) and random modes. Without realistic feed curation that distinguishes in-network from out-of-network content, experiments cannot isolate the effect of algorithmic amplification on information spread.

### Solution Summary

Port key elements from X's open-sourced recommendation algorithm to enable realistic feed curation. This includes candidate sourcing (splitting in-network vs out-of-network), applying documented heuristic scale factors (OON penalty, reply penalty, author diversity decay), and providing a configurable ranking mode alongside existing modes.

### Business Value

| Benefit | Impact |
|---------|--------|
| Realistic feed simulation | Enables valid experimental comparisons (Study 1, Study 2) |
| Configurable ranking modes | A/B testing between x_algo, preference, random |
| Author diversity control | Prevents feed domination by single authors |
| Research credibility | Uses documented scale factors from X's actual algorithm |

## User Stories

### Researcher

**As a researcher**, I want to configure the feed algorithm mode, so that I can run controlled experiments comparing algorithmic vs random feeds.

**Acceptance Criteria:**
- Can set `ranking.mode` to `x_algo`, `preference`, or `random` in config
- X-algo mode applies documented scale factors from X's algorithm
- Preference mode works as before (similarity only)
- Random mode works as before (uniform sampling)

### Simulation Operator

**As a simulation operator**, I want agents to receive feeds that distinguish between followed and discovered content, so that in-network effects can be measured.

**Acceptance Criteria:**
- Agents have a `following` set of agent IDs they follow
- In-network posts (from followed agents) receive no penalty
- Out-of-network posts receive configurable scale factor (default 0.75)
- Feed shows mix of both candidate sources

### Data Analyst

**As a data analyst**, I want feeds to have author diversity controls, so that a single prolific author doesn't dominate feeds.

**Acceptance Criteria:**
- Repeat author posts are penalized with exponential decay
- Decay factor is configurable (default 0.5)
- Floor prevents complete suppression (default 0.25)
- First occurrence of each author has no penalty

## Functional Requirements

### FR-1: Candidate Sourcing

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | In-network candidates are posts from agents the requesting agent follows |
| FR-1.2 | Out-of-network candidates are discovered via RAG similarity search |
| FR-1.3 | Candidate limits are configurable (default 50 each) |
| FR-1.4 | Empty following set treats all candidates as out-of-network |

### FR-2: Heuristic Rescoring

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | Base score from embedding similarity (converted from distance) |
| FR-2.2 | Out-of-network scale factor applied (default 0.75) |
| FR-2.3 | Reply scale factor applied for posts with parent (default 0.75) |
| FR-2.4 | Scale factors multiply, not add |

### FR-3: Author Diversity

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | Track author occurrence count within a single feed generation |
| FR-3.2 | Apply decay^occurrence penalty for repeat authors |
| FR-3.3 | Floor prevents decay below minimum (default 0.25) |
| FR-3.4 | Reset occurrence counts for each new feed request |

### FR-4: Configuration

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | `RankingConfig` model with all scale factor fields |
| FR-4.2 | YAML config section `ranking:` in config files |
| FR-4.3 | Mode selection: `x_algo`, `preference`, `random` |
| FR-4.4 | Validation on scale factors (0.0-1.0 range where applicable) |

### FR-5: Social Graph

| Requirement | Description |
|-------------|-------------|
| FR-5.1 | `SocialAgent.following` field of type `set[str]` |
| FR-5.2 | `SocialGraph` protocol for follow relationship queries |
| FR-5.3 | Integration with `SimulationState` for graph access |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Feed generation latency | < 100ms for 100-post candidate pool |
| Memory overhead | < 1KB per agent for following set |
| Scaling | Support 500 agents with 100 follows each |

### Maintainability

| Requirement | Target |
|-------------|--------|
| Test coverage | > 90% for ranking module |
| Type annotations | All public APIs fully typed |
| Documentation | Docstrings on all public classes/methods |

## Scope

### In Scope

- `RankingConfig` Pydantic model with validated scale factors
- `XAlgorithmRanker` class implementing ranking pipeline
- `SocialGraph` protocol and simple implementation
- `SocialAgent.following` field extension
- `Post.parent_id` field for reply detection
- Integration with existing `FeedRetriever` for base scores
- YAML configuration support
- Unit tests for all components

### Out of Scope

- Full production-grade recommendation system
- ML-based heavy ranker (using embedding similarity as approximation)
- Real-time engagement features (using static post metrics)
- User feedback factors ("show more"/"show less")
- Multi-task learning normalization

### Future Considerations

- Engagement velocity as a scoring factor
- Media boost factors (images, video)
- Source diversity (beyond author diversity)
- Configurable candidate proportions (in-network vs OON ratio)

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Mode switching | 3 modes work | Config test |
| Scale factor application | Matches X algorithm | Unit tests |
| Author diversity | Decay applied correctly | Unit tests |
| Integration | Works with simulation loop | Integration test |

## Assumptions

1. X's documented scale factors are stable and representative
2. Embedding similarity is an adequate proxy for ML ranking scores
3. Static post metrics suffice (no real-time engagement updates)
4. Social graph is provided at simulation setup time

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Social graph complexity | Medium | Medium | Start with simple following set |
| ChromaDB score access | Low | High | Verify `include=["distances"]` works |
| Config migration | Low | Low | Backward-compatible defaults |
| Performance at scale | Low | Medium | Benchmark with 500 agents early |

## Glossary

| Term | Definition |
|------|------------|
| In-network (INN) | Posts from agents the requesting agent follows |
| Out-of-network (OON) | Posts discovered via similarity, not from followed agents |
| Scale factor | Multiplicative modifier applied to base score |
| Author diversity | Mechanism to prevent feed domination by single authors |
| Heavy ranker | ML model in X's pipeline (approximated with similarity here) |
