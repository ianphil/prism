# Specification: Simulation Workflow Loop

## Overview

### Problem Statement

PRISM has working components (LLM clients, RAG feed system, statecharts) but no way to run an actual simulation. The components exist in isolation - there's no orchestration layer to coordinate agents making decisions, update shared state, or produce the emergent behavior that is the core value of the system.

Without this feature, PRISM is a collection of building blocks that cannot be used for research.

### Solution Summary

Implement a simulation workflow that orchestrates agent rounds through a sequential executor pipeline: feed retrieval → agent decision → state update → logging. The workflow is controlled by a round controller that iterates through N rounds with M agents, managing turn order and checkpointing state for reproducibility.

### Business Value

| Benefit | Impact |
|---------|--------|
| Enable research | Users can finally run simulations to study virality |
| Reproducibility | Checkpointing enables replay and debugging of specific rounds |
| Observability | Per-round state distribution enables analysis of emergent patterns |
| Configuration-driven | YAML config enables parameter sweeps without code changes |

## User Stories

### US-1: Researcher Runs Basic Simulation

**As a researcher**, I want to run a simulation with configurable agents and rounds, so that I can observe emergent engagement patterns.

**Acceptance Criteria:**
- AC-1.1: Can specify number of agents (10-500) and rounds (1-100) via config
- AC-1.2: Simulation executes all rounds without manual intervention
- AC-1.3: Per-round state distribution is logged (agents per state)
- AC-1.4: Final metrics include total likes, reshares, replies across all posts

### US-2: Researcher Resumes From Checkpoint

**As a researcher**, I want to resume a simulation from a checkpoint, so that I can debug or extend a partially completed run.

**Acceptance Criteria:**
- AC-2.1: Checkpoints are saved after each round (configurable frequency)
- AC-2.2: Checkpoints include full state: posts, agents, metrics, round number
- AC-2.3: Simulation can resume from any checkpoint JSON file
- AC-2.4: Resumed simulation produces identical results to uninterrupted run

### US-3: Developer Understands Agent Decisions

**As a developer**, I want decision logs that show trigger → state → action, so that I can debug agent behavior.

**Acceptance Criteria:**
- AC-3.1: Each agent decision logs: agent_id, round, trigger, from_state, to_state
- AC-3.2: Reasoner invocations are logged separately with options and choice
- AC-3.3: Logs are structured (JSON lines) for programmatic analysis

### US-4: Researcher Observes State Distribution

**As a researcher**, I want per-round state distribution metrics, so that I can analyze how agent behavior evolves over time.

**Acceptance Criteria:**
- AC-4.1: After each round, log distribution of agents across all states
- AC-4.2: Distribution is available in checkpoint for post-hoc analysis
- AC-4.3: Can query current distribution during simulation via API

## Functional Requirements

### FR-1: Simulation State Management

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | `SimulationState` class tracks posts, agents, round number, and metrics |
| FR-1.2 | Posts list grows as agents compose new content |
| FR-1.3 | Engagement metrics (likes, reshares, replies) update as agents engage |
| FR-1.4 | State distribution computed using existing `state_distribution()` function |
| FR-1.5 | All state is Pydantic-serializable for checkpointing |

### FR-2: Executor Pipeline

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | `FeedRetrievalExecutor` wraps `FeedRetriever.get_feed()` for each agent |
| FR-2.2 | `AgentDecisionExecutor` uses `Statechart.fire()` + `Reasoner` for decisions |
| FR-2.3 | `StateUpdateExecutor` applies decision actions (new post, engagement increment) |
| FR-2.4 | `LoggingExecutor` records decision + state transition to structured log |
| FR-2.5 | Executors are async for future parallelization |

### FR-3: Agent Decision Flow

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | Call `agent.tick()` at start of each round |
| FR-3.2 | Check `agent.is_timed_out()` for timeout trigger |
| FR-3.3 | Determine trigger based on agent state and context |
| FR-3.4 | Fire statechart transition; invoke reasoner if multiple targets |
| FR-3.5 | Call `agent.transition_to()` to record state change |
| FR-3.6 | Execute action based on new state (compose, like, reply, reshare, scroll) |

### FR-4: Round Controller

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | Configure max rounds, agents per round, checkpoint frequency |
| FR-4.2 | Iterate rounds 0 to max_rounds-1 |
| FR-4.3 | Process all agents each round (sequential MVP, parallel future) |
| FR-4.4 | Save checkpoint after each round (or per frequency setting) |
| FR-4.5 | Support resume from checkpoint |
| FR-4.6 | Return final `SimulationResult` with metrics summary |

### FR-5: Checkpointing

| Requirement | Description |
|-------------|-------------|
| FR-5.1 | Checkpoint includes: round_number, posts, agents, metrics, state_distribution |
| FR-5.2 | Serialize to JSON using Pydantic model serialization |
| FR-5.3 | File naming: `checkpoint_round_{N}.json` |
| FR-5.4 | Configurable output directory |
| FR-5.5 | Resume loads checkpoint, reconstructs state, continues from round N+1 |

### FR-6: Configuration

| Requirement | Description |
|-------------|-------------|
| FR-6.1 | Extend `configs/default.yaml` with `simulation:` section |
| FR-6.2 | Config includes: max_rounds, checkpoint_frequency, checkpoint_dir |
| FR-6.3 | Config includes: parallelism (1 for MVP, >1 future) |
| FR-6.4 | Config includes: reasoner_enabled (true/false) |
| FR-6.5 | `SimulationConfig` Pydantic model for validation |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| NFR-1 | Single agent round < 5s (dominated by LLM inference) |
| NFR-2 | 100 agents × 50 rounds < 7 hours (sequential) |
| NFR-3 | Checkpoint write < 1s for 500 agents |
| NFR-4 | Memory: < 4GB for 500 agents, 10K posts |

### Reliability

| Requirement | Target |
|-------------|--------|
| NFR-5 | Checkpoint on crash allows resume within 1 round of failure |
| NFR-6 | Agent decision failure → default to SCROLL, log warning |
| NFR-7 | Reasoner failure → fallback to first valid target |

### Observability

| Requirement | Target |
|-------------|--------|
| NFR-8 | Every decision logged with structured JSON |
| NFR-9 | Per-round metrics available in memory and checkpoint |
| NFR-10 | State distribution logged after each round |

## Scope

### In Scope

- `SimulationState` class with posts, agents, metrics, checkpointing
- Sequential executor pipeline (feed → decision → state → logging)
- Statechart-driven agent decisions with reasoner integration
- Round controller with checkpoint/resume support
- Configuration via YAML + Pydantic model
- Structured JSON logging of decisions and state transitions
- Default social media statechart factory function

### Out of Scope

- X algorithm ranking (Feature 005 - plugs into feed step later)
- OpenTelemetry tracing integration (Feature 006)
- Parallel agent processing (future enhancement)
- CLI with batch mode (Feature 007)
- Real-time visualization

### Future Considerations

- Parallel agent batching with asyncio.gather()
- Agent warm-up period before engagement
- Variable turn order (random shuffle vs round-robin)
- Binary checkpoint format for large simulations

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Simulation completes | 100 agents × 50 rounds | End-to-end test |
| Checkpoint/resume works | Resume produces same final state | Deterministic seed test |
| State distribution logged | All 8 states per round | Log parsing test |
| Decisions use statechart | No direct decide() calls | Code review |
| Config validation | Invalid config rejected | Unit tests |

## Assumptions

1. Sequential processing is acceptable for MVP (parallel later)
2. 500 agents is upper bound for single-machine simulation
3. JSON checkpoints are sufficient (binary optimization future)
4. Agent Framework OllamaChatClient remains stable API
5. ChromaDB can handle 10K posts efficiently

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM inference too slow | High | Medium | Use faster model (Mistral) for dev; parallelize later |
| Memory exhaustion | Medium | High | Lazy loading of agent history; limit post retention |
| Checkpoint corruption | Low | High | Write to temp file, atomic rename |
| Statechart edge cases | Medium | Medium | Extensive guard testing; fallback to SCROLL |

## Glossary

| Term | Definition |
|------|------------|
| Round | One iteration where all agents make one decision each |
| Executor | Component that performs one step of the agent pipeline |
| Checkpoint | JSON snapshot of simulation state at a round boundary |
| Trigger | Event name that initiates a statechart transition (e.g., "sees_post") |
| Guard | Boolean function that must return True for transition to fire |
