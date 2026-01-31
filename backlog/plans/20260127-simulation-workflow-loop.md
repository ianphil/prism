---
title: "Simulation Workflow Loop"
status: open
priority: high
created: 2026-01-27
depends_on: ["001-foundation-agent-ollama", "002-rag-feed-system", "003-agent-behavior-statecharts"]
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
   - `agent_decision`: **Statechart-driven** — fire triggers, evaluate guards, invoke reasoner for ambiguous cases
   - `state_update`: Apply actions (new posts, engagement increments)
   - `logging`: Record decisions and **state transitions** for analysis
2. **State Manager**: Tracks posts, engagement counts, agent action history, **agent state distribution**
3. **Round Controller**: Iterates rounds, manages agent turn order, handles parallelism, **ticks agent timers**
4. **Checkpointing**: Serialize state between rounds for resume/replay

## Statechart Integration

Feature 3 (`003-agent-behavior-statecharts/`) provides the agent behavior model. Key integration points:

| Component | Integration |
|-----------|-------------|
| `Statechart.fire()` | Replaces direct `decide()` calls — determines state transitions |
| `agent.tick()` | Called each round to track time-in-state |
| `agent.is_timed_out()` | Checked before firing — triggers timeout recovery |
| `Reasoner` | Invoked when multiple transitions are valid |
| `agent.transition_to()` | Records state change + history after fire() |
| `state_distribution()` | Query for observability each round |

**Flow per agent per round:**
```
tick() → is_timed_out()? → determine_trigger() → fire() → [reasoner?] → transition_to()
```

See `backlog/plans/_completed/003-agent-behavior-statecharts/plan.md` for detailed architecture.

## Tasks

- [ ] Define `SimulationState` class (posts, agents, round number, metrics, state distribution)
- [ ] Implement trigger determination logic (maps agent state → appropriate trigger)
- [ ] Implement feed retrieval executor (calls `FeedRetriever` per agent)
- [ ] Implement agent round executor (tick → timeout check → fire → reasoner → transition_to)
- [ ] Implement state update executor (apply actions, update engagement)
- [ ] Implement logging executor (record decisions + state transitions to structured log)
- [ ] Build workflow graph connecting all executors
- [ ] Add state distribution tracking per round (for observability)
- [ ] Add checkpointing (JSON/pickle state snapshots per round)
