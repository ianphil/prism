# PRISM Implementation Order

This document outlines the recommended implementation sequence for PRISM based on the PRD and feature dependencies.

## Feature Overview

| # | Feature | Plan File | Priority | Est. Tasks | Status |
|---|---------|-----------|----------|------------|--------|
| 1 | Foundation: Agent Framework + Ollama | `_completed/001-foundation-agent-ollama/` | High | 14 | ✅ Done |
| 2 | RAG Feed System | `_completed/002-rag-feed-system/` | High | 30 | ✅ Done |
| 3 | Agent Behavior Statecharts | `003-agent-behavior-statecharts/` | High | 47 | Planned |
| 4 | Simulation Workflow Loop | `20260127-simulation-workflow-loop.md` | High | 7 | Open |
| 5 | X Algorithm Ranking | `20260127-x-algorithm-ranking.md` | Medium | 6 | Open |
| 6 | Data Pipeline | `20260127-data-pipeline.md` | Medium | 7 | Open |
| 7 | Observability and Metrics | `20260127-observability-metrics.md` | Medium | 7 | Open |
| 8 | Experiment Framework | `20260127-experiment-framework.md` | Medium | 7 | Open |

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌───────────┐                                             │
│   │ Feature 1 │  Foundation: Agent Framework + Ollama  ✅   │
│   │   (Done)  │  No dependencies - COMPLETE                 │
│   └─────┬─────┘                                             │
│         │                                                   │
│    ┌────┴────┬──────────────┐                               │
│    │         │              │                               │
│    ▼         ▼              ▼                               │
│ ┌─────┐  ┌─────┐        ┌─────┐                             │
│ │ F2  │  │ F6  │        │ F3  │                             │
│ │ RAG │  │Data │        │State│  Agent Behavior             │
│ │Feed │  │Pipe │        │chart│  Statecharts                │
│ └──┬──┘  └──┬──┘        └──┬──┘                             │
│    │        │              │                                │
│    ▼        │              │                                │
│ ┌─────┐     │              │                                │
│ │ F5  │     │              │                                │
│ │X Alg│     │              │                                │
│ └──┬──┘     │              │                                │
│    │        │              │                                │
│    ▼        ▼              ▼                                │
│ ┌──────────────────────────────┐                            │
│ │         Feature 4            │                            │
│ │    Simulation Workflow Loop  │  (depends on F2, F3)       │
│ │          (High)              │                            │
│ └──────────────┬───────────────┘                            │
│                │                                            │
│                ▼                                            │
│ ┌──────────────────────────────┐                            │
│ │         Feature 7            │  Observability and Metrics │
│ │          (Medium)            │                            │
│ └──────────────┬───────────────┘                            │
│                │                                            │
│                ▼                                            │
│ ┌──────────────────────────────┐                            │
│ │         Feature 8            │  Experiment Framework      │
│ │          (Medium)            │  (capstone)                │
│ └──────────────────────────────┘                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Recommended Implementation Sequence

### Phase 1: Core Infrastructure ✅ COMPLETE

**Feature 1: Foundation**
- Microsoft Agent Framework + Ollama integration
- Basic `ChatAgent` with gpt-oss:20b
- `IChatClient` abstraction for LLM provider flexibility
- Validates: Single agent can make decisions

### Phase 2: Data Layer & Agent Behavior (Current)

**Feature 2: RAG Feed System** (depends on F1) — ✅ Complete
- ChromaDB vector store setup
- Post embedding and retrieval
- Preference-based and random feed modes
- Validates: Agent receives relevant posts

**Feature 3: Agent Behavior Statecharts** (depends on F1, parallel with F2) — *Planned*
- Harel-style statechart for agent behavioral states
- Shared statechart with parameterized guards per agent
- LLM as decision oracle for ambiguous transitions
- Timeout transitions for stuck agents
- State history in agent memory for RAG context
- Validates: Agent states are queryable, transitions are traceable

**Feature 6: Data Pipeline** (depends on F1, parallel with F2/F3)
- Twitter dataset ingestion
- Bot filtering and trait inference
- Agent profile generation
- Validates: Real data bootstraps realistic agents

### Phase 3: Simulation Core

**Feature 4: Simulation Workflow Loop** (depends on F2, F3)
- Graph-based workflow orchestration
- Statechart-driven agent execution per round
- State management and checkpointing
- Validates: Multi-agent simulation runs end-to-end

**Feature 5: X Algorithm Ranking** (depends on F2, parallel with F4)
- Candidate sourcing (in-network + out-of-network)
- Ranking score with velocity and media boosts
- Configurable feed modes
- Validates: Algorithmic feed differs from random

### Phase 4: Analysis Layer

**Feature 7: Observability and Metrics** (depends on F4)
- OpenTelemetry tracing integration
- Cascade tracking with NetworkX
- Virality metrics (size, depth, velocity)
- Agent state distribution over time
- Validates: Full trace coverage, metrics export

### Phase 5: Experimentation

**Feature 8: Experiment Framework** (depends on F4, F5, F7)
- CLI for running simulations
- A/B testing with batch replications
- pyDOE/SALib integration for DOE
- Analysis pipeline with stats and plots
- Validates: End-to-end hypothesis testing

## Parallel Work Opportunities

Some features can be developed concurrently:

| Track A (Feed Path) | Track B (Agent Path) | Track C (Data Path) |
|---------------------|----------------------|---------------------|
| F2 (RAG) | F3 (Statecharts) | F6 (Data Pipeline) |
| F5 (X Algorithm) | — | — |

After F1 (complete):
- **Track A**: F2 (RAG) → F5 (X Algorithm) — feed retrieval and ranking
- **Track B**: F3 (Statecharts) — agent behavior model
- **Track C**: F6 (Data Pipeline) — can run independently

Merge point: F4 (Simulation Loop) requires F2 + F3, optionally F5/F6
- **After F4**: F7 (Observability) → F8 (Experiments)

## Milestones and Validation Gates

| Milestone | Features Complete | Validation |
|-----------|-------------------|------------|
| **M1: Agent Works** | F1 ✅ | Single agent makes valid decision with gpt-oss:20b |
| **M2: Feed Works** | F1, F2 ✅ | Agent receives personalized feed from ChromaDB |
| **M3: States Work** | F1, F3 | Agent transitions between states, state queries work |
| **M4: Sim Runs** | F1-F4 | 100-agent statechart-driven simulation completes 10 rounds |
| **M5: Real Data** | F1-F4, F6 | Simulation bootstrapped from Twitter dataset |
| **M6: Algorithm** | F1-F5 | X-algo feed produces different cascades than random |
| **M7: Observable** | F1-F5, F7 | 100% trace coverage, state distributions exported |
| **M8: Experiments** | F1-F8 | Visuals hypothesis A/B test completes |

## Risk Mitigation by Phase

| Phase | Key Risk | Mitigation |
|-------|----------|------------|
| 1 | Agent Framework API instability | Pin versions, abstract behind interfaces ✅ |
| 2 | ChromaDB performance at scale | Benchmark early with 10K posts |
| 3 | Statechart complexity creep | Start with shared parameterized model, resist per-type charts |
| 4 | Memory pressure with 500 agents | Streaming inference, lazy loading, limit state history depth |
| 5 | X algo heuristics unclear | Start simple, iterate based on results |
| 6 | Twitter data format variations | Configurable schema mapping |
| 7 | Trace overhead impacts performance | Sample traces in production runs |
| 8 | Experiment runtime too long | Use Mistral for dev, gpt-oss:20b for final |

## Next Steps

1. ~~Start with Feature 1: Foundation~~ ✅ Complete
2. ~~Continue Feature 2 (RAG)~~ ✅ Complete
3. ~~Plan Feature 3 (Statecharts) with `/planner`~~ ✅ Planned (47 tasks)
4. Implement Feature 3 with `/implement` skill
5. Track progress in `backlog/plans/` with status updates
6. Validate each milestone before proceeding
