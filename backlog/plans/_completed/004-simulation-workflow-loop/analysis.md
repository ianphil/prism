# Simulation Workflow Loop Analysis

## Executive Summary

This feature implements the core simulation orchestration layer that connects all existing PRISM components (LLM clients, RAG feed system, statecharts) into a working round-based simulation. The workflow coordinates agent decisions through statechart-driven state transitions, manages shared simulation state, and provides checkpointing for reproducibility.

| Pattern | Integration Point |
|---------|-------------------|
| Graph-based workflow | New `prism/simulation/` module with executors |
| State management | `SimulationState` aggregating posts, agents, metrics |
| Statechart-driven decisions | Existing `Statechart.fire()` replaces direct `decide()` calls |
| Round controller | Iterates rounds, manages turn order, ticks agent timers |
| Checkpointing | JSON serialization of `SimulationState` per round |

## Architecture Comparison

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Current PRISM Components                      │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  prism/llm/      │  │  prism/rag/      │  │ prism/        │  │
│  │  • OllamaClient  │  │  • FeedRetriever │  │ statechart/   │  │
│  │  • LLMConfig     │  │  • Post model    │  │ • Statechart  │  │
│  │  • as_agent()    │  │  • ChromaDB      │  │ • Reasoner    │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│                                ▼                                 │
│                   ┌──────────────────────┐                       │
│                   │  prism/agents/       │                       │
│                   │  • SocialAgent       │                       │
│                   │  • decide()          │                       │
│                   │  • tick(), transition│                       │
│                   └──────────────────────┘                       │
│                                                                  │
│  ❌ No orchestration layer connecting these components          │
│  ❌ No simulation loop executing rounds                         │
│  ❌ No shared state management                                   │
│  ❌ No checkpointing for reproducibility                        │
└─────────────────────────────────────────────────────────────────┘
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Target PRISM Architecture                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  prism/simulation/ (NEW)                  │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │              RoundController                      │    │   │
│  │  │  • run_simulation(config)                         │    │   │
│  │  │  • for round in range(max_rounds)                 │    │   │
│  │  │    • for agent in agents                          │    │   │
│  │  │      • execute(agent, state) → pipeline           │    │   │
│  │  └──────────────────┬───────────────────────────────┘    │   │
│  │                     │                                     │   │
│  │  ┌─────────────────┴─────────────────────────────────┐   │   │
│  │  │              Executor Pipeline                     │   │   │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐     │   │   │
│  │  │  │   Feed     │→│   Agent    │→│   State    │     │   │   │
│  │  │  │ Retrieval  │ │  Decision  │ │   Update   │     │   │   │
│  │  │  └────────────┘ └────────────┘ └────────────┘     │   │   │
│  │  │        │              │              │             │   │   │
│  │  │        │              │              │             │   │   │
│  │  │        │              │              ▼             │   │   │
│  │  │        │              │       ┌────────────┐       │   │   │
│  │  │        │              │       │  Logging   │       │   │   │
│  │  │        │              │       └────────────┘       │   │   │
│  │  └────────┼──────────────┼─────────────────────────── │   │   │
│  │           │              │                             │   │   │
│  │  ┌────────┴──────────────┴──────────────────────────┐ │   │   │
│  │  │              SimulationState                      │ │   │   │
│  │  │  • posts: list[Post]                              │ │   │   │
│  │  │  • agents: list[SocialAgent]                      │ │   │   │
│  │  │  • round_number: int                              │ │   │   │
│  │  │  • engagement_metrics: EngagementMetrics          │ │   │   │
│  │  │  • state_distribution: dict[AgentState, int]      │ │   │   │
│  │  │  • checkpoint() / restore()                       │ │   │   │
│  │  └───────────────────────────────────────────────────┘ │   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ prism/llm/   │  │ prism/rag/   │  │ prism/statechart/   │    │
│  │ (existing)   │  │ (existing)   │  │ (existing)          │    │
│  └──────────────┘  └──────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Pattern Mapping

### 1. Agent Decision Flow

**Current Implementation (Feature 001-003):**

```python
# Direct LLM call bypasses statechart
decision = await agent.decide(feed_text)  # Returns AgentDecision
```

**Target Evolution:**

```python
# Statechart-driven decision with reasoner for ambiguous cases
agent.tick()  # Increment time-in-state
if agent.is_timed_out():
    trigger = "timeout"
else:
    trigger = determine_trigger(agent, feed, state)

new_state = statechart.fire(trigger, agent.state, agent, context)
if new_state is None and reasoner_enabled:
    targets = statechart.valid_targets(agent.state, trigger)
    if len(targets) > 1:
        new_state = await reasoner.decide(agent, agent.state, trigger, targets, context)

if new_state:
    agent.transition_to(new_state, trigger, context)
    # Execute action based on new_state (compose, engage, etc.)
```

### 2. Feed Retrieval Integration

**Current Implementation (Feature 002):**

```python
retriever = FeedRetriever(collection, feed_size=5, default_mode="preference")
feed = retriever.get_feed(interests=agent.interests)
```

**Target Evolution:**

```python
# Feed executor wraps existing retriever
class FeedRetrievalExecutor:
    async def execute(self, agent: SocialAgent, state: SimulationState) -> list[Post]:
        return self.retriever.get_feed(interests=agent.interests)
```

### 3. State Management

**Current Implementation:**

Individual components track their own state:
- `SocialAgent.state_history` - agent's own transitions
- `FeedRetriever` - posts in ChromaDB
- No aggregated simulation state

**Target Evolution:**

Centralized `SimulationState` manages:
- All posts (new + existing)
- All agents (with their individual states)
- Round counter
- Engagement metrics (likes, reshares, replies aggregated)
- State distribution per round (for observability)
- Checkpointing to JSON

### 4. Workflow Orchestration

**Current Implementation:**

No orchestration exists. The PRD shows conceptual workflow:

```python
# From PRD (not implemented)
workflow = Workflow()
workflow.add_executor("feed_retrieval", feed_retriever)
workflow.add_executor("agent_decision", agent_pool)
workflow.add_edge(Edge("feed_retrieval", "agent_decision"))
```

**Target Evolution:**

Simple sequential executor pipeline (no external workflow library):

```python
class AgentRoundExecutor:
    """Executes one agent's turn in the simulation."""

    async def execute(self, agent: SocialAgent, state: SimulationState) -> RoundResult:
        # 1. Feed retrieval
        feed = await self.feed_executor.execute(agent, state)

        # 2. Agent decision (statechart-driven)
        decision = await self.decision_executor.execute(agent, feed, state)

        # 3. State update
        await self.state_executor.execute(agent, decision, state)

        # 4. Log the result
        await self.logging_executor.execute(agent, decision, state)

        return RoundResult(agent_id=agent.agent_id, decision=decision)
```

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| `OllamaChatClient` | ✅ | Feature 001 - LLM inference |
| `SocialAgent` | ✅ | Feature 001/003 - agent with state, history, tick/timeout |
| `AgentDecision` | ✅ | Feature 001 - structured decision output |
| `FeedRetriever` | ✅ | Feature 002 - RAG feed with preference/random modes |
| `Post` model | ✅ | Feature 002 - with media, engagement metrics |
| `Statechart` | ✅ | Feature 003 - fire(), valid_triggers(), valid_targets() |
| `StatechartReasoner` | ✅ | Feature 003 - LLM-based ambiguous transition resolution |
| `AgentState` enum | ✅ | Feature 003 - IDLE, SCROLLING, EVALUATING, etc. |
| `state_distribution()` | ✅ | Feature 003 - query function for observability |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| `SimulationState` | ❌ | New - aggregates posts, agents, metrics, round |
| `SimulationConfig` | ❌ | New - YAML-driven configuration |
| `RoundController` | ❌ | New - iterates rounds, manages turn order |
| `FeedRetrievalExecutor` | ❌ | New - wraps FeedRetriever |
| `AgentDecisionExecutor` | ❌ | New - statechart-driven decision |
| `StateUpdateExecutor` | ❌ | New - applies actions to state |
| `LoggingExecutor` | ❌ | New - records decisions + transitions |
| `Checkpointer` | ❌ | New - JSON serialization |
| Trigger determination | ❌ | New - maps agent context to trigger |
| Default transition config | ❌ | New - standard social media statechart |

## Key Insights

### What Works Well

1. **Statechart foundation is solid** - The `Statechart.fire()` method already handles guard evaluation, first-match semantics, and action execution. The simulation loop just needs to call it.

2. **SocialAgent has all state tracking** - `state`, `state_history`, `tick()`, `is_timed_out()`, and `transition_to()` are already implemented. No modifications needed to agent class.

3. **RAG system is complete** - `FeedRetriever.get_feed()` handles both preference and random modes with ChromaDB. Just wrap it in an executor.

4. **Reasoner handles ambiguous cases** - `StatechartReasoner.decide()` already prompts the LLM and parses responses for multi-target transitions.

5. **Query functions exist** - `state_distribution(agents)` already computes what we need for per-round observability.

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| No default statechart transitions defined | Create `create_social_media_statechart()` factory with standard triggers/guards |
| No trigger determination logic | Map agent state + context to appropriate trigger (sees_post, decides, composes, etc.) |
| SocialAgent.decide() bypasses statechart | New decision executor uses statechart.fire() + reasoner instead |
| No engagement metric aggregation | `EngagementMetrics` dataclass tracking likes/reshares/replies per round |
| No checkpointing | `Checkpointer` class with JSON serialization using Pydantic |
| main.py is empty | Wire up RoundController with CLI-style entry point |
| No configuration for simulation params | Extend configs/default.yaml with simulation section |

### Design Considerations

1. **Simple pipeline over workflow library** - The PRD mentions Agent Framework workflows, but we'll implement a simple sequential pipeline. This avoids external dependencies and keeps the code understandable.

2. **Statechart is shared, parameterized** - One statechart definition shared by all agents. Agent-specific behavior comes from:
   - `engagement_threshold` in guards
   - `personality`/`interests` in reasoner decisions

3. **Trigger determination is key** - The mapping from agent context to trigger name is critical:
   - `IDLE → sees_feed → SCROLLING`
   - `SCROLLING → sees_post → EVALUATING`
   - `EVALUATING → decides → COMPOSING | SCROLLING`
   - etc.

4. **Checkpoints are JSON for debugging** - Human-readable JSON allows inspection and replay. Later can add more efficient binary format if needed.
