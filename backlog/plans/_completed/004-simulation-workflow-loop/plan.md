# Plan: Simulation Workflow Loop

## Summary

Implement the core simulation orchestration that connects PRISM's existing components (LLM client, RAG feed, statecharts) into a working round-based simulation. The workflow executes a sequential pipeline (feed → decision → state → logging) for each agent in each round, with statechart-driven decisions and JSON checkpointing for reproducibility.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      prism/simulation/                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     RoundController                             │ │
│  │  • run_simulation(config, agents, initial_posts)                │ │
│  │  • run_round(state) → SimulationState                           │ │
│  │  • resume_from_checkpoint(path) → SimulationState               │ │
│  └─────────────────────────┬──────────────────────────────────────┘ │
│                            │                                         │
│               for round in range(max_rounds):                        │
│               for agent in state.agents:                             │
│                            │                                         │
│                            ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   AgentRoundExecutor                            │ │
│  │  async execute(agent, state) → RoundResult                      │ │
│  │                                                                  │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │ │
│  │  │     Feed     │→│   Decision   │→│    State     │            │ │
│  │  │  Retrieval   │ │   Executor   │ │   Update     │            │ │
│  │  │   Executor   │ │              │ │   Executor   │            │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │ │
│  │         │               │                │                       │ │
│  │         │               │                ▼                       │ │
│  │         │               │         ┌──────────────┐              │ │
│  │         │               │         │   Logging    │              │ │
│  │         │               │         │   Executor   │              │ │
│  │         │               │         └──────────────┘              │ │
│  └─────────┼───────────────┼────────────────────────────────────── │ │
│            │               │                                         │
│            │               ▼                                         │
│  ┌─────────┼────────────────────────────────────────────────────── │
│  │         │         SimulationState                                │ │
│  │         │  ┌─────────────────────────────────────────────────┐  │ │
│  │         │  │ • posts: list[Post]                             │  │ │
│  │         │  │ • agents: list[SocialAgent]                     │  │ │
│  │         │  │ • round_number: int                             │  │ │
│  │         │  │ • metrics: EngagementMetrics                    │  │ │
│  │         │  │ • statechart: Statechart                        │  │ │
│  │         │  │ • reasoner: StatechartReasoner                  │  │ │
│  │         │  └─────────────────────────────────────────────────┘  │ │
│  │         │                                                        │ │
│  │         ▼                                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                       │ │
│  │  │  FeedRetriever  │  │   Checkpointer  │                       │ │
│  │  │  (from rag/)    │  │  • save(state)  │                       │ │
│  │  │                 │  │  • load(path)   │                       │ │
│  │  └─────────────────┘  └─────────────────┘                       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Architecture

### Executor Pipeline Flow

```
    Agent Round Execution (per agent, per round)
    ═══════════════════════════════════════════

    ┌───────────────────────────────────────────────────────────────┐
    │                  AgentRoundExecutor.execute()                  │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ 1. FeedRetrievalExecutor                                       │
    │    retriever.get_feed(interests=agent.interests)               │
    │    → list[Post]                                                │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ 2. AgentDecisionExecutor                                       │
    │    a. agent.tick()                                             │
    │    b. if agent.is_timed_out(): trigger = "timeout"             │
    │       else: trigger = determine_trigger(agent, feed)           │
    │    c. new_state = statechart.fire(trigger, agent.state, ...)   │
    │    d. if new_state is None and multiple targets:               │
    │         new_state = await reasoner.decide(...)                 │
    │    e. if new_state: agent.transition_to(new_state, trigger)    │
    │    f. action = execute_state_action(agent, new_state, feed)    │
    │    → DecisionResult(new_state, action, trigger)                │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ 3. StateUpdateExecutor                                         │
    │    if action.type == "compose":                                │
    │        state.posts.append(new_post)                            │
    │        retriever.add_post(new_post)                            │
    │    elif action.type == "like":                                 │
    │        target_post.likes += 1                                  │
    │        state.metrics.total_likes += 1                          │
    │    elif action.type == "reply":                                │
    │        state.posts.append(reply_post)                          │
    │        target_post.replies += 1                                │
    │    elif action.type == "reshare":                              │
    │        state.posts.append(reshare_post)                        │
    │        target_post.reshares += 1                               │
    │    → None (mutates state in place)                             │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ 4. LoggingExecutor                                             │
    │    log_entry = {                                               │
    │        "round": state.round_number,                            │
    │        "agent_id": agent.agent_id,                             │
    │        "trigger": trigger,                                     │
    │        "from_state": old_state.value,                          │
    │        "to_state": new_state.value,                            │
    │        "action_type": action.type,                             │
    │        "timestamp": datetime.now(UTC).isoformat()              │
    │    }                                                           │
    │    logger.info(json.dumps(log_entry))                          │
    │    → None                                                      │
    └───────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `SimulationState` | Aggregates posts, agents, metrics, round | All executors |
| `SimulationConfig` | YAML-driven configuration | RoundController |
| `RoundController` | Orchestrates rounds, checkpointing | AgentRoundExecutor, Checkpointer |
| `AgentRoundExecutor` | Coordinates executor pipeline | All executors |
| `FeedRetrievalExecutor` | Wraps FeedRetriever | FeedRetriever, SimulationState |
| `AgentDecisionExecutor` | Statechart-driven decisions | Statechart, Reasoner, SocialAgent |
| `StateUpdateExecutor` | Applies actions to state | SimulationState, FeedRetriever |
| `LoggingExecutor` | Structured JSON logging | Python logging |
| `Checkpointer` | JSON serialization | SimulationState |
| `create_social_media_statechart()` | Factory for default transitions | Statechart, Transition |

### Data Flow: Agent Scrolls Feed and Reshares

```
RoundController               AgentRoundExecutor              FeedRetriever
      │                             │                              │
      │ run_round(state)            │                              │
      │─────────────────────────────│                              │
      │  for agent in agents:       │                              │
      │      execute(agent, state)  │                              │
      │             │               │                              │
      │             ▼               │                              │
      │        ┌────────────────────▼──────────────────────────┐   │
      │        │ 1. feed_executor.execute(agent, state)        │   │
      │        │    retriever.get_feed(agent.interests)        │──▶│
      │        │                                               │◀──│
      │        │    → [Post1, Post2, Post3, ...]               │   │
      │        └───────────────────┬───────────────────────────┘   │
      │                            │
      │                            ▼
      │        ┌───────────────────────────────────────────────┐
      │        │ 2. decision_executor.execute(agent, feed)     │
      │        │    agent.tick()  → ticks_in_state = 3         │
      │        │    is_timed_out()? → False                    │
      │        │    determine_trigger() → "sees_post"          │
      │        │    statechart.fire("sees_post", SCROLLING)    │
      │        │    → EVALUATING                               │
      │        │    agent.transition_to(EVALUATING, "sees_post")│
      │        │    determine_trigger() → "decides"            │
      │        │    statechart.fire("decides", EVALUATING)     │
      │        │    → [COMPOSING, SCROLLING] (ambiguous)       │
      │        │    reasoner.decide(...) → ENGAGING_RESHARE    │
      │        │    agent.transition_to(ENGAGING_RESHARE)      │
      │        │    → DecisionResult(ENGAGING_RESHARE, reshare)│
      │        └───────────────────┬───────────────────────────┘
      │                            │
      │                            ▼
      │        ┌───────────────────────────────────────────────┐
      │        │ 3. state_executor.execute(decision, state)    │
      │        │    post.reshares += 1                         │
      │        │    state.metrics.total_reshares += 1          │
      │        │    state.posts.append(reshare_post)           │
      │        └───────────────────┬───────────────────────────┘
      │                            │
      │                            ▼
      │        ┌───────────────────────────────────────────────┐
      │        │ 4. logging_executor.execute(result)           │
      │        │    → JSON log entry                           │
      │        └───────────────────────────────────────────────┘
      │                            │
      │◀───────────────────────────│
      │
      │ checkpoint(state) if round % frequency == 0
      └────────────────────────────────────────────────────────────
```

## File Structure

```
prism/
├── simulation/                   # NEW: Simulation orchestration module
│   ├── __init__.py               # NEW: Export public API
│   ├── config.py                 # NEW: SimulationConfig Pydantic model
│   ├── state.py                  # NEW: SimulationState, EngagementMetrics
│   ├── controller.py             # NEW: RoundController
│   ├── executors/                # NEW: Executor pipeline
│   │   ├── __init__.py           # NEW: Export executors
│   │   ├── base.py               # NEW: BaseExecutor protocol
│   │   ├── feed.py               # NEW: FeedRetrievalExecutor
│   │   ├── decision.py           # NEW: AgentDecisionExecutor
│   │   ├── state_update.py       # NEW: StateUpdateExecutor
│   │   └── logging.py            # NEW: LoggingExecutor
│   ├── checkpointer.py           # NEW: JSON checkpoint save/load
│   ├── triggers.py               # NEW: determine_trigger() logic
│   └── statechart_factory.py     # NEW: create_social_media_statechart()
│
├── statechart/
│   └── (existing files)          # No modifications needed
│
├── agents/
│   └── social_agent.py           # MODIFY: Add optional statechart param
│
configs/
└── default.yaml                  # MODIFY: Add simulation section

tests/
├── simulation/                   # NEW: Simulation tests
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_state.py
│   ├── test_controller.py
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── test_feed.py
│   │   ├── test_decision.py
│   │   ├── test_state_update.py
│   │   └── test_logging.py
│   ├── test_checkpointer.py
│   ├── test_triggers.py
│   ├── test_statechart_factory.py
│   └── test_integration.py
```

## Critical: Trigger Determination Logic

**Problem**: How do we map agent state + context to the appropriate trigger for the statechart?

**Solution**: A `determine_trigger()` function that encodes the state machine's event model:

```python
def determine_trigger(agent: SocialAgent, feed: list[Post], state: SimulationState) -> str:
    """Determine the trigger to fire based on agent state and context."""

    match agent.state:
        case AgentState.IDLE:
            return "start_browsing"  # → SCROLLING

        case AgentState.SCROLLING:
            if feed:  # Has posts to look at
                return "sees_post"   # → EVALUATING
            else:
                return "feed_empty"  # → RESTING

        case AgentState.EVALUATING:
            return "decides"         # → COMPOSING | ENGAGING_* | SCROLLING

        case AgentState.COMPOSING:
            return "finishes_composing"  # → SCROLLING

        case AgentState.ENGAGING_LIKE | AgentState.ENGAGING_REPLY | AgentState.ENGAGING_RESHARE:
            return "finishes_engaging"   # → SCROLLING

        case AgentState.RESTING:
            return "rested"          # → IDLE

        case _:
            return "unknown"
```

The statechart has corresponding transitions for each trigger from each state.

## Implementation Phases

See `tasks.md` for detailed breakdown. Summary:

1. **Phase 1: State Foundation** - SimulationConfig, SimulationState, EngagementMetrics
2. **Phase 2: Trigger & Statechart Factory** - determine_trigger(), create_social_media_statechart()
3. **Phase 3: Executors** - Feed, Decision, StateUpdate, Logging executors
4. **Phase 4: Controller & Checkpoint** - RoundController, Checkpointer, resume logic
5. **Phase 5: Integration** - End-to-end test, main.py entry point

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sequential vs parallel | Sequential MVP | Simpler to debug; parallel is future enhancement |
| Workflow library | No external deps | Agent Framework adds complexity without benefit |
| Checkpoint format | JSON | Human-readable, debuggable; binary later if needed |
| Trigger model | Explicit function | Clear mapping from state to trigger; easy to test |
| State mutation | In-place | Executors mutate SimulationState; simpler than immutable |
| Logging format | JSON lines | Structured, parseable; grep-friendly |

## Configuration Example

```yaml
# configs/default.yaml additions
simulation:
  max_rounds: 50                  # Number of rounds to execute
  checkpoint_frequency: 1         # Checkpoint every N rounds (1 = every round)
  checkpoint_dir: outputs/checkpoints  # Where to save checkpoints
  reasoner_enabled: true          # Whether to use LLM for ambiguous transitions
  log_decisions: true             # Log every agent decision to JSON
  log_file: outputs/decisions.jsonl  # Decision log file path
```

## Files to Modify

| File | Change |
|------|--------|
| `configs/default.yaml` | Add `simulation:` section |
| `prism/agents/social_agent.py` | Minor: ensure Pydantic serialization works |
| `main.py` | Wire up RoundController entry point |

## New Files

| File | Purpose |
|------|---------|
| `prism/simulation/__init__.py` | Module exports |
| `prism/simulation/config.py` | SimulationConfig Pydantic model |
| `prism/simulation/state.py` | SimulationState, EngagementMetrics |
| `prism/simulation/controller.py` | RoundController orchestration |
| `prism/simulation/executors/` | Executor pipeline components |
| `prism/simulation/checkpointer.py` | JSON save/load |
| `prism/simulation/triggers.py` | determine_trigger() function |
| `prism/simulation/statechart_factory.py` | create_social_media_statechart() |

## Verification

1. Unit tests pass: `uv run pytest tests/simulation/`
2. Integration test: 10 agents × 5 rounds completes successfully
3. Checkpoint test: Resume produces same final state as uninterrupted
4. State distribution: Logged correctly each round
5. Spec tests pass: `specs/tests/004-simulation-workflow-loop.md`

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM inference slow | Use Mistral 7B for dev; gpt-oss:20b for production |
| Memory exhaustion | Limit history depth; lazy load agent context |
| Checkpoint corruption | Write to temp file, atomic rename |
| Statechart edge cases | Extensive guard tests; fallback to SCROLL |
| Complex trigger logic | Clear match statement; unit test all cases |

## Limitations (MVP)

1. **Sequential processing only** - No parallel agent batching. Acceptable for development; will add asyncio.gather() later.

2. **No warm-up period** - Agents start immediately in IDLE. Could add configurable warm-up rounds.

3. **Fixed turn order** - All agents process in list order each round. Could add shuffle option.

4. **JSON checkpoints only** - May be slow for 500+ agents. Binary format is future optimization.

5. **No cascade tracking** - NetworkX analysis is post-simulation. Could integrate later.

## References

- [PRISM PRD §4.2](../../aidocs/prd.md) - Simulation Orchestration requirements
- [Feature 003 Plan](../_completed/003-agent-behavior-statecharts/plan.md) - Statechart integration
- [W3C SCXML](https://www.w3.org/TR/scxml/) - State machine semantics reference
