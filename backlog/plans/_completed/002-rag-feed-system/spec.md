# Specification: RAG Feed System with ChromaDB

## Overview

### Problem Statement

Social agents currently receive feed content as hardcoded strings passed directly to `SocialAgent.decide()`. This approach cannot:
- Personalize feeds based on agent interests
- Retrieve posts dynamically from a growing corpus
- Support different retrieval strategies (preference vs random)
- Track post engagement metrics that evolve during simulation

Without a proper feed retrieval system, agents cannot make realistic decisions based on their personalities, and experiments cannot compare algorithmic vs random feed curation.

### Solution Summary

Implement a RAG-based feed retrieval system using ChromaDB as the vector store. The system embeds and indexes posts, retrieves relevant posts based on agent interests (preference mode) or uniformly samples recent posts (random mode), and formats them for agent prompts with visual media indicators.

### Business Value

| Benefit | Impact |
|---------|--------|
| Personalized feeds | Agents see content aligned with their interests, producing realistic engagement patterns |
| Controlled experiments | Toggle between preference/random modes to measure algorithmic effects |
| Scalable content storage | ChromaDB handles thousands of posts with efficient similarity search |
| Media simulation | Agents react to visual content indicators, enabling the visual virality hypothesis |

## User Stories

### Researcher

**As a researcher**, I want agents to receive personalized feeds based on their interests, so that the simulation produces realistic engagement cascades.

**Acceptance Criteria:**
- Agent with interests ["crypto", "technology"] sees more crypto/tech posts
- Retrieval uses cosine similarity between agent interests and post embeddings
- Feed contains 5-10 posts per agent turn (configurable)

### Experimenter

**As an experimenter**, I want to switch between preference-based and random feed modes, so that I can measure the impact of algorithmic curation on virality.

**Acceptance Criteria:**
- Config parameter `mode: preference | random` controls retrieval strategy
- Random mode uniformly samples from recent posts
- Mode can be changed per simulation run via config

### Developer

**As a developer**, I want posts to be stored with media flags and engagement metrics, so that agents can make decisions about visual content and popular posts.

**Acceptance Criteria:**
- Post model includes `has_media`, `media_type`, `media_description` fields
- Post model includes `likes`, `reshares`, `replies`, `velocity` metrics
- Feed rendering shows media indicators and engagement stats to agents

## Functional Requirements

### FR-1: Post Data Model

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | `Post` class is a Pydantic model with id, author_id, text, timestamp |
| FR-1.2 | `Post` includes media simulation fields: has_media, media_type, media_description |
| FR-1.3 | `Post` includes engagement metrics: likes, reshares, replies, velocity |
| FR-1.4 | All fields have appropriate types and defaults per PRD §4.4 |

### FR-2: RAG Configuration

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | `RAGConfig` model with collection_name, embedding_model, persist_directory |
| FR-2.2 | `RAGConfig` includes feed_size (1-20) and mode (preference/random) |
| FR-2.3 | `PrismConfig` extended with `rag: RAGConfig` section |
| FR-2.4 | Config loads from YAML with defaults for all RAG fields |

### FR-3: ChromaDB Integration

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | Factory function creates/connects to ChromaDB collection |
| FR-3.2 | Collection uses configurable embedding function (Ollama or sentence-transformers) |
| FR-3.3 | Supports both in-memory and persistent storage via config |

### FR-4: Post Storage

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | `add_post(post: Post)` embeds and indexes a post in ChromaDB |
| FR-4.2 | Posts stored with metadata for filtering (author_id, timestamp, has_media) |
| FR-4.3 | `add_posts(posts: list[Post])` batch inserts multiple posts |

### FR-5: Feed Retrieval

| Requirement | Description |
|-------------|-------------|
| FR-5.1 | `FeedRetriever.get_feed()` returns list of Post objects |
| FR-5.2 | Preference mode queries by agent interests embedding |
| FR-5.3 | Random mode uniformly samples from recent posts |
| FR-5.4 | Returns configurable number of posts (feed_size) |

### FR-6: Feed Rendering

| Requirement | Description |
|-------------|-------------|
| FR-6.1 | `format_feed_for_prompt(posts)` renders posts as agent-readable text |
| FR-6.2 | Includes media indicators with emoji format per PRD (📷, 🎬, etc.) |
| FR-6.3 | Includes engagement stats (❤️ likes, 🔁 reshares, 💬 replies) |
| FR-6.4 | Includes relative timestamp (e.g., "3h ago") |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Embedding latency | < 500ms per post (Ollama), < 100ms (sentence-transformers) |
| Retrieval latency | < 200ms for 10 posts from 10K corpus |
| Memory footprint | In-memory collection supports 50K posts on 16GB RAM |

### Scalability

| Requirement | Target |
|-------------|--------|
| Post corpus size | Support 100K posts with persistent storage |
| Concurrent retrievals | Safe for single-threaded simulation loop |

### Reliability

| Requirement | Target |
|-------------|--------|
| Missing embedding model | Graceful error with instructions to pull model |
| ChromaDB unavailable | Clear error message on collection creation failure |

## Scope

### In Scope

- `Post` Pydantic model with all PRD-specified fields
- `RAGConfig` with collection, embedding, and retrieval settings
- ChromaDB collection creation and management
- Post storage with embeddings and metadata
- Preference-based retrieval (cosine similarity on interests)
- Random retrieval (uniform sampling)
- Feed rendering with media and engagement indicators
- Unit tests for all components
- Integration tests with actual ChromaDB

### Out of Scope

- X algorithm ranking integration (Feature 4)
- Simulation loop orchestration (Feature 3)
- Post creation/generation (Feature 5 data pipeline)
- Agent profile storage (posts indexed, agents are transient)
- Real-time indexing updates during retrieval
- Multi-collection support

### Future Considerations

- Hybrid retrieval combining preference and X algorithm scores
- Time-decay weighting for "recent" posts
- Agent-specific exclusions (posts already seen)
- Embedding model fine-tuning

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retrieval accuracy | Preference mode returns relevant posts | Manual inspection of top-5 similarity |
| Mode switching | Random mode returns diverse posts | Entropy of post topics > threshold |
| Media rendering | Agent sees formatted media indicators | Prompt includes [📷 IMAGE: ...] blocks |
| Configuration | All settings configurable via YAML | Load config, change values, observe behavior |

## Assumptions

1. ChromaDB Python client is stable and compatible with Python 3.11+
2. Ollama `nomic-embed-text` or sentence-transformers provides adequate embedding quality
3. 5-10 posts per feed is sufficient context for agent decisions
4. Posts are indexed before retrieval (no streaming/real-time updates during a query)
5. Agent interests are available as a list of topic strings

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ChromaDB API changes | Low | Medium | Pin chromadb version; abstract behind FeedRetriever |
| Embedding model unavailable | Medium | High | Default to sentence-transformers; provide setup instructions |
| Similarity search returns irrelevant posts | Medium | Medium | Tune embedding model; validate with test cases |
| Memory pressure with large corpus | Low | Medium | Support persistent storage; document memory limits |

## Glossary

| Term | Definition |
|------|------------|
| RAG | Retrieval-Augmented Generation — retrieving relevant context before LLM inference |
| Embedding | Dense vector representation of text for similarity search |
| ChromaDB | Open-source embedding database for AI applications |
| Feed | List of posts presented to an agent for decision-making |
| Preference mode | Retrieval based on similarity to agent interests |
| Random mode | Uniform sampling from post corpus |
| Velocity | Rate of engagement growth, used for X algorithm ranking |
