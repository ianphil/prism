# Data Model: Simulation Workflow Loop

## Entities

### SimulationConfig

Configuration for running a simulation, loaded from YAML.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| max_rounds | int | No | 50 | Number of rounds to execute |
| checkpoint_frequency | int | No | 1 | Save checkpoint every N rounds |
| checkpoint_dir | str | None | None | Directory for checkpoints (None = no save) |
| reasoner_enabled | bool | No | True | Use LLM for ambiguous transitions |
| log_decisions | bool | No | True | Log decisions to JSON file |
| log_file | str | None | None | Path for decision log (None = no file) |

**Invariants:**
- `max_rounds >= 1`
- `checkpoint_frequency >= 1`

---

### EngagementMetrics

Aggregated engagement metrics for the simulation.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| total_likes | int | No | 0 | Cumulative likes across all posts |
| total_reshares | int | No | 0 | Cumulative reshares |
| total_replies | int | No | 0 | Cumulative replies |
| posts_created | int | No | 0 | New posts created by agents |

**Relationships:**
- Owned by one `SimulationState`

**Invariants:**
- All fields >= 0

---

### SimulationState

Central state container for the simulation.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| round_number | int | No | 0 | Current round (0-indexed) |
| posts | list[Post] | Yes | - | All posts (initial + generated) |
| agents | list[SocialAgent] | Yes | - | All agents in simulation |
| metrics | EngagementMetrics | No | EngagementMetrics() | Aggregated metrics |
| statechart | Statechart | Yes | - | Shared statechart definition |
| reasoner | StatechartReasoner | None | None | LLM reasoner (None if disabled) |

**Relationships:**
- Contains N `Post` objects
- Contains M `SocialAgent` objects
- References one `Statechart`
- Optionally references one `StatechartReasoner`

**Invariants:**
- `round_number >= 0`
- `len(agents) >= 1` (at least one agent)

---

### DecisionResult

Result from the decision executor for one agent turn.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| agent_id | str | Yes | - | Agent that made the decision |
| trigger | str | Yes | - | Trigger that was fired |
| from_state | AgentState | Yes | - | State before transition |
| to_state | AgentState | Yes | - | State after transition |
| action | ActionResult | None | None | Action taken (if any) |
| reasoner_used | bool | No | False | Whether reasoner was invoked |

**Relationships:**
- Produced by `AgentDecisionExecutor`
- May contain one `ActionResult`

---

### ActionResult

Result of an action taken by an agent.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| action_type | str | Yes | - | Type: "compose", "like", "reply", "reshare", "scroll" |
| target_post_id | str | None | None | Post being engaged with |
| new_post | Post | None | None | New post if action created one |
| content | str | None | None | Content for reply/reshare |

**Invariants:**
- If `action_type in ["like", "reply", "reshare"]`, then `target_post_id` is required
- If `action_type in ["compose", "reply", "reshare"]`, then `new_post` is set
- If `action_type == "scroll"`, all optional fields are None

---

### RoundResult

Aggregated result for one simulation round.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| round_number | int | Yes | - | Round that was executed |
| decisions | list[DecisionResult] | Yes | - | Decision for each agent |
| state_distribution | dict[AgentState, int] | Yes | - | Agent distribution after round |
| duration_ms | int | No | 0 | Round execution time |

**Relationships:**
- Contains N `DecisionResult` objects (one per agent)

---

### SimulationResult

Final result after simulation completes.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| total_rounds | int | Yes | - | Number of rounds executed |
| final_metrics | EngagementMetrics | Yes | - | Final engagement metrics |
| final_state_distribution | dict[AgentState, int] | Yes | - | Agent distribution at end |
| total_duration_ms | int | No | 0 | Total execution time |
| checkpoint_path | str | None | None | Path to final checkpoint |

---

### CheckpointData

Serializable snapshot of simulation state.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| version | str | No | "1.0" | Checkpoint format version |
| round_number | int | Yes | - | Round at checkpoint |
| posts | list[dict] | Yes | - | Serialized posts |
| agents | list[dict] | Yes | - | Serialized agent state |
| metrics | dict | Yes | - | Serialized metrics |
| state_distribution | dict[str, int] | Yes | - | Distribution (state.value → count) |
| timestamp | str | Yes | - | ISO timestamp of checkpoint |

**Invariants:**
- `version` must match loader's expected version

---

## State Transitions

### Agent State Machine Flow

```
                         start_browsing
                ┌─────────────────────────────────┐
                │                                 │
                ▼                                 │
            ┌───────┐     rested              ┌───────┐
            │ IDLE  │◀────────────────────────│RESTING│
            └───┬───┘                         └───▲───┘
                │                                 │
                │ start_browsing                  │ feed_empty
                ▼                                 │
           ┌─────────┐                            │
       ┌──▶│SCROLLING│────────────────────────────┘
       │   └────┬────┘
       │        │
       │        │ sees_post
       │        ▼
       │   ┌──────────┐
       │   │EVALUATING│
       │   └────┬─────┘
       │        │
       │        │ decides
       │        ▼
       │   ┌─────────────────────────────────────────┐
       │   │  [Guard/Reasoner selects target]         │
       │   │                                          │
       │   │  ┌─────────┐   ┌──────────────┐         │
       │   │  │COMPOSING│   │ENGAGING_LIKE │         │
       │   │  └────┬────┘   └──────┬───────┘         │
       │   │       │               │                  │
       │   │  ┌────┴───────────────┴──────┐          │
       │   │  │  finishes_engaging         │          │
       │   │  │  finishes_composing        │          │
       │   │  └────────────┬───────────────┘          │
       │   │               │                          │
       │   │  ┌────────────┴────────────┐            │
       │   │  │ ENGAGING_REPLY          │            │
       │   │  │ ENGAGING_RESHARE        │            │
       │   │  └─────────────────────────┘            │
       │   └──────────────┬──────────────────────────┘
       │                  │
       └──────────────────┘
```

### Trigger → State Mapping

| Current State | Trigger | Target States | Guard/Reasoner |
|---------------|---------|---------------|----------------|
| IDLE | start_browsing | SCROLLING | Always |
| SCROLLING | sees_post | EVALUATING | has_posts(feed) |
| SCROLLING | feed_empty | RESTING | !has_posts(feed) |
| EVALUATING | decides | COMPOSING | high_engagement_guard |
| EVALUATING | decides | ENGAGING_LIKE | like_tendency_guard |
| EVALUATING | decides | ENGAGING_REPLY | reply_tendency_guard |
| EVALUATING | decides | ENGAGING_RESHARE | reshare_tendency_guard |
| EVALUATING | decides | SCROLLING | low_engagement_guard |
| COMPOSING | finishes_composing | SCROLLING | Always |
| ENGAGING_* | finishes_engaging | SCROLLING | Always |
| RESTING | rested | IDLE | Always |
| * | timeout | SCROLLING | is_timed_out() |

---

## Data Flow

### Round Execution Flow

```
RoundController.run_round(state)
        │
        │ for agent in state.agents:
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ AgentRoundExecutor.execute(agent, state)                       │
│                                                                │
│   ┌───────────────────────────────────────────────────────┐   │
│   │ FeedRetrievalExecutor.execute(agent, state)           │   │
│   │   retriever.get_feed(agent.interests)                 │   │
│   │   → list[Post]                                        │   │
│   └─────────────────────────┬─────────────────────────────┘   │
│                             │                                  │
│   ┌─────────────────────────▼─────────────────────────────┐   │
│   │ AgentDecisionExecutor.execute(agent, feed, state)     │   │
│   │   1. agent.tick()                                     │   │
│   │   2. trigger = determine_trigger(agent, feed)         │   │
│   │   3. new_state = statechart.fire(trigger, ...)        │   │
│   │   4. if ambiguous: new_state = reasoner.decide(...)   │   │
│   │   5. agent.transition_to(new_state, trigger)          │   │
│   │   6. action = execute_action(agent, new_state, feed)  │   │
│   │   → DecisionResult                                    │   │
│   └─────────────────────────┬─────────────────────────────┘   │
│                             │                                  │
│   ┌─────────────────────────▼─────────────────────────────┐   │
│   │ StateUpdateExecutor.execute(decision, state)          │   │
│   │   - Mutate post engagement counts                     │   │
│   │   - Add new posts to state.posts                      │   │
│   │   - Update state.metrics                              │   │
│   │   → None                                              │   │
│   └─────────────────────────┬─────────────────────────────┘   │
│                             │                                  │
│   ┌─────────────────────────▼─────────────────────────────┐   │
│   │ LoggingExecutor.execute(decision, state)              │   │
│   │   - Write JSON log entry                              │   │
│   │   → None                                              │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                                │
│   → RoundResult (per agent)                                    │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
    state.round_number += 1
    checkpoint_if_needed(state)
    → RoundResult (aggregated)
```

---

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| SimulationConfig | max_rounds >= 1 | ValueError("max_rounds must be >= 1") |
| SimulationConfig | checkpoint_frequency >= 1 | ValueError("checkpoint_frequency must be >= 1") |
| SimulationState | len(agents) >= 1 | ValueError("simulation requires at least one agent") |
| ActionResult | like/reply/reshare requires target_post_id | ValueError("target_post_id required") |
| CheckpointData | version matches expected | ValueError("unsupported checkpoint version") |
