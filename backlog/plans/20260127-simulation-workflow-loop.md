---
title: "Simulation Workflow Loop"
status: open
priority: high
created: 2026-01-27
depends_on: ["001-foundation-agent-ollama", "20260127-rag-feed-system.md", "20260130-agent-behavior-statecharts.md"]
---

# Simulation Workflow Loop

## Summary

Implement the core simulation orchestration using Agent Framework's graph-based workflows, connecting feed retrieval, agent decisions, state updates, and logging in a configurable round-robin loop.

## Motivation

This is the heart of PRISM. The simulation loop coordinates hundreds of agents making decisions each round, updating shared state, and producing the emergent behavior we want to study. Without this, we have components but no simulation.

## Proposal

### Goals

- Build graph-based workflow connecting: feed → decision → state → logging
- Support round-robin iteration (50-100 rounds, 250-500 agents)
- Implement state management for posts, engagement metrics, agent memories
- Enable checkpointing and replay for debugging
- Configure parallelism for agent batching

### Non-Goals

- X algorithm ranking (Feature 4 - plugs into feed step later)
- OpenTelemetry integration (Feature 6)
- Experiment CLI and batch modes (Feature 7)

## Design

Per PRD §4.2, the workflow is a directed graph:

1. **Workflow Graph**: Four executors connected sequentially
   - `feed_retrieval`: Queries RAG system for each agent's feed
   - `agent_decision`: Batch LLM inference via agent pool
   - `state_update`: Apply actions (new posts, engagement increments)
   - `logging`: Record decisions for analysis
2. **State Manager**: Tracks posts, engagement counts, agent action history
3. **Round Controller**: Iterates rounds, manages agent turn order, handles parallelism
4. **Checkpointing**: Serialize state between rounds for resume/replay

## Tasks

- [ ] Define `SimulationState` class (posts, agents, round number, metrics)
- [ ] Implement feed retrieval executor (calls `FeedRetriever` per agent)
- [ ] Implement agent decision executor (batch inference with parallelism config)
- [ ] Implement state update executor (apply actions, update engagement)
- [ ] Implement logging executor (record decisions to structured log)
- [ ] Build workflow graph connecting all executors
- [ ] Add checkpointing (JSON/pickle state snapshots per round)
