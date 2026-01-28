---
title: "RAG Feed System with ChromaDB"
status: open
priority: high
created: 2026-01-27
depends_on: ["20260127-foundation-agent-framework-ollama.md"]
---

# RAG Feed System with ChromaDB

## Summary

Implement the RAG-based feed retrieval system using ChromaDB, enabling agents to receive personalized or random post feeds based on configurable retrieval modes.

## Motivation

Agents need context to make decisions. The feed system provides each agent with relevant posts to evaluate, forming the input for their engage/ignore/reply/reshare decisions. This is the bridge between stored content and agent reasoning.

## Proposal

### Goals

- Set up ChromaDB as the vector store for posts and embeddings
- Implement feed retrieval with two modes: preference-based and random
- Create the `Post` dataclass with media simulation fields per PRD
- Support configurable retrieval (5-10 candidate posts per agent turn)
- Index all generated content for future retrievals

### Non-Goals

- X algorithm ranking integration (Feature 4)
- Full simulation loop orchestration (Feature 3)
- Twitter data ingestion (Feature 5)

## Design

Architecture follows PRD §4.4:

1. **Vector Store**: ChromaDB collection for posts, using sentence-transformers or Ollama embedding models
2. **Post Model**: Dataclass with id, author, text, timestamp, media flags, engagement metrics, velocity
3. **Feed Retriever**: Configurable class supporting:
   - **Preference mode**: Cosine similarity between agent interests and post embeddings
   - **Random mode**: Uniform sampling from recent posts
4. **Embedding Pipeline**: Embed posts on creation, store in ChromaDB with metadata
5. **Feed Rendering**: Format retrieved posts for agent prompts (including media indicators)

## Tasks

- [ ] Install ChromaDB: `pip install chromadb`
- [ ] Define `Post` dataclass per PRD spec (media_type, media_description, metrics)
- [ ] Implement embedding utility using sentence-transformers
- [ ] Create ChromaDB collection with post schema and metadata
- [ ] Implement `FeedRetriever` class with preference and random modes
- [ ] Add feed rendering for agent prompts (format posts with engagement stats)
- [ ] Write tests: embedding, retrieval accuracy, mode switching
