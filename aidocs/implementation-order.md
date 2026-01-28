# PRISM Implementation Order

This document outlines the recommended implementation sequence for PRISM based on the PRD and feature dependencies.

## Feature Overview

| # | Feature | Plan File | Priority | Est. Tasks |
|---|---------|-----------|----------|------------|
| 1 | Foundation: Agent Framework + Ollama | `20260127-foundation-agent-framework-ollama.md` | High | 7 |
| 2 | RAG Feed System | `20260127-rag-feed-system.md` | High | 7 |
| 3 | Simulation Workflow Loop | `20260127-simulation-workflow-loop.md` | High | 7 |
| 4 | X Algorithm Ranking | `20260127-x-algorithm-ranking.md` | Medium | 6 |
| 5 | Data Pipeline | `20260127-data-pipeline.md` | Medium | 7 |
| 6 | Observability and Metrics | `20260127-observability-metrics.md` | Medium | 7 |
| 7 | Experiment Framework | `20260127-experiment-framework.md` | Medium | 7 |

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌───────────┐                                             │
│   │ Feature 1 │  Foundation: Agent Framework + Ollama       │
│   │   (High)  │  No dependencies - START HERE               │
│   └─────┬─────┘                                             │
│         │                                                   │
│    ┌────┴────┬──────────────┐                               │
│    │         │              │                               │
│    ▼         ▼              ▼                               │
│ ┌─────┐  ┌─────┐        ┌─────┐                             │
│ │ F2  │  │ F5  │        │     │                             │
│ │ RAG │  │Data │        │     │                             │
│ │Feed │  │Pipe │        │     │                             │
│ └──┬──┘  └──┬──┘        │     │                             │
│    │        │           │     │                             │
│    ▼        │           │     │                             │
│ ┌─────┐     │           │     │                             │
│ │ F4  │     │           │     │                             │
│ │X Alg│─────┼───────────┘     │                             │
│ └──┬──┘     │                 │                             │
│    │        │                 │                             │
│    ▼        ▼                 │                             │
│ ┌──────────────┐              │                             │
│ │   Feature 3  │◄─────────────┘                             │
│ │  Simulation  │  Workflow Loop (core orchestration)        │
│ │    (High)    │                                            │
│ └──────┬───────┘                                            │
│        │                                                    │
│        ▼                                                    │
│ ┌──────────────┐                                            │
│ │   Feature 6  │  Observability and Metrics                 │
│ │   (Medium)   │                                            │
│ └──────┬───────┘                                            │
│        │                                                    │
│        ▼                                                    │
│ ┌──────────────┐                                            │
│ │   Feature 7  │  Experiment Framework (capstone)           │
│ │   (Medium)   │                                            │
│ └──────────────┘                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Recommended Implementation Sequence

### Phase 1: Core Infrastructure (Weeks 1-2)

**Feature 1: Foundation**
- Microsoft Agent Framework + Ollama integration
- Basic `ChatAgent` with gpt-oss:20b
- `IChatClient` abstraction for LLM provider flexibility
- Validates: Single agent can make decisions

### Phase 2: Data Layer (Weeks 3-4)

**Feature 2: RAG Feed System** (depends on F1)
- ChromaDB vector store setup
- Post embedding and retrieval
- Preference-based and random feed modes
- Validates: Agent receives relevant posts

**Feature 5: Data Pipeline** (depends on F1, parallel with F2)
- Twitter dataset ingestion
- Bot filtering and trait inference
- Agent profile generation
- Validates: Real data bootstraps realistic agents

### Phase 3: Simulation Core (Weeks 4-5)

**Feature 3: Simulation Workflow Loop** (depends on F1, F2)
- Graph-based workflow orchestration
- Round-robin agent execution
- State management and checkpointing
- Validates: Multi-agent simulation runs end-to-end

**Feature 4: X Algorithm Ranking** (depends on F2, parallel with F3)
- Candidate sourcing (in-network + out-of-network)
- Ranking score with velocity and media boosts
- Configurable feed modes
- Validates: Algorithmic feed differs from random

### Phase 4: Analysis Layer (Weeks 6-7)

**Feature 6: Observability and Metrics** (depends on F3)
- OpenTelemetry tracing integration
- Cascade tracking with NetworkX
- Virality metrics (size, depth, velocity)
- Validates: Full trace coverage, metrics export

### Phase 5: Experimentation (Weeks 8-10)

**Feature 7: Experiment Framework** (depends on F3, F4, F6)
- CLI for running simulations
- A/B testing with batch replications
- pyDOE/SALib integration for DOE
- Analysis pipeline with stats and plots
- Validates: End-to-end hypothesis testing

## Parallel Work Opportunities

Some features can be developed concurrently:

| Parallel Track A | Parallel Track B |
|------------------|------------------|
| F1 → F2 → F3 | F1 → F5 |
| F2 → F4 | - |

After F1 completes:
- **Track A**: F2 (RAG) → F3 (Simulation) → F6 (Observability) → F7 (Experiments)
- **Track B**: F5 (Data Pipeline) can run independently
- **Track C**: F4 (X Algorithm) can start after F2, merge into F3

## Milestones and Validation Gates

| Milestone | Features Complete | Validation |
|-----------|-------------------|------------|
| **M1: Agent Works** | F1 | Single agent makes valid decision with gpt-oss:20b |
| **M2: Feed Works** | F1, F2 | Agent receives personalized feed from ChromaDB |
| **M3: Sim Runs** | F1, F2, F3 | 100-agent simulation completes 10 rounds |
| **M4: Real Data** | F1, F2, F3, F5 | Simulation bootstrapped from Twitter dataset |
| **M5: Algorithm** | F1-F4 | X-algo feed produces different cascades than random |
| **M6: Observable** | F1-F4, F6 | 100% trace coverage, metrics exported |
| **M7: Experiments** | F1-F7 | Visuals hypothesis A/B test completes |

## Risk Mitigation by Phase

| Phase | Key Risk | Mitigation |
|-------|----------|------------|
| 1 | Agent Framework API instability | Pin versions, abstract behind interfaces |
| 2 | ChromaDB performance at scale | Benchmark early with 10K posts |
| 3 | Memory pressure with 500 agents | Streaming inference, lazy loading |
| 4 | X algo heuristics unclear | Start simple, iterate based on results |
| 5 | Twitter data format variations | Configurable schema mapping |
| 6 | Trace overhead impacts performance | Sample traces in production runs |
| 7 | Experiment runtime too long | Use Mistral for dev, gpt-oss:20b for final |

## Next Steps

1. Start with Feature 1: Foundation
2. Use `/planner` for detailed TDD task breakdown on each feature
3. Track progress in `backlog/plans/` with status updates
4. Validate each milestone before proceeding
