# Agent Behavior Statecharts Analysis

## Executive Summary

| Pattern | Integration Point |
|---------|-------------------|
| Pydantic models | `AgentState` enum mirrors `AgentDecision.choice` pattern |
| Dataclass patterns | `Transition` follows `Post` field structure |
| LLM oracle | Statechart uses `SocialAgent._agent.run()` for ambiguous transitions |
| Async operations | State transitions follow `SocialAgent.decide()` async pattern |
| Agent profile | Statechart guards use agent interests/personality thresholds |

## Architecture Comparison

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  PRISM (Features 001-002)                   │
│                                                             │
│  SocialAgent                                                │
│      │                                                      │
│      ├── decide(feed_text) ──▶ LLM ──▶ AgentDecision       │
│      │       │                                              │
│      │       └── Stateless: each call is independent        │
│      │                                                      │
│      └── No behavioral state tracking                       │
│          • Can't query "how many agents composing?"         │
│          • No behavioral momentum between decisions         │
│          • No traceable state transitions for debugging     │
└─────────────────────────────────────────────────────────────┘

Problem: Agent behavior is opaque. The LLM's "state" is implicit
         in its reasoning, making it impossible to:
         - Debug cascade formation
         - Query agent state distribution
         - Model behavioral patterns (lurking → engaging)
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PRISM (Feature 003)                                 │
│                                                                      │
│  Statechart (shared definition)                                      │
│      │                                                               │
│      ├── states: {Idle, Scrolling, Evaluating, Composing, Engaging} │
│      ├── transitions: [{trigger, source, target, guard, action}]     │
│      └── fire(agent, trigger, context) → new_state | None            │
│                                                                      │
│  SocialAgent                                                         │
│      │                                                               │
│      ├── state: AgentState = Idle                                    │
│      ├── state_history: list[StateTransition]                        │
│      │                                                               │
│      └── decide(post) ──┬──▶ Statechart.fire(self, trigger, post)   │
│                         │         │                                  │
│                         │         ▼                                  │
│                         │    Guard evaluation (agent thresholds)     │
│                         │         │                                  │
│                         │    ┌────┴────┐                             │
│                         │    │         │                             │
│                         │  clear    ambiguous                        │
│                         │    │         │                             │
│                         │    ▼         ▼                             │
│                         │  direct   LLM Oracle                       │
│                         │  transition  │                             │
│                         │    │         │                             │
│                         │    └────┬────┘                             │
│                         │         ▼                                  │
│                         └──▶ new state + record in history           │
│                                                                      │
│  State Queries                                                       │
│      • agents_in_state(state) → count                                │
│      • state_distribution() → {state: count}                         │
│      • agent.state_history → list[StateTransition]                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Pattern Mapping

### 1. State Enum Pattern

**Current Implementation:**
```python
# prism/agents/decision.py
class AgentDecision(BaseModel):
    choice: Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
```

**Target Evolution:**
```python
# prism/statechart/states.py
from enum import Enum

class AgentState(str, Enum):
    IDLE = "idle"
    SCROLLING = "scrolling"
    EVALUATING = "evaluating"
    COMPOSING = "composing"
    ENGAGING_LIKE = "engaging_like"
    ENGAGING_REPLY = "engaging_reply"
    ENGAGING_RESHARE = "engaging_reshare"
    RESTING = "resting"
```

Same pattern: constrained set of valid values using enum.

### 2. Dataclass/Model Pattern

**Current Implementation:**
```python
# prism/rag/models.py
class Post(BaseModel):
    id: str
    author_id: str
    text: str
    timestamp: datetime
    # ... fields with defaults and validation
```

**Target Evolution:**
```python
# prism/statechart/transitions.py
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Transition:
    trigger: str
    source: AgentState
    target: AgentState
    guard: Callable[[Any, Any], bool] | None = None
    action: Callable[[Any, Any], None] | None = None
```

Dataclass pattern for simple structured data with optional fields.

### 3. Async Decision Pattern

**Current Implementation:**
```python
# prism/agents/social_agent.py
async def decide(self, feed_text: str) -> AgentDecision:
    response = await self._agent.run(...)
    return AgentDecision(...)
```

**Target Evolution:**
```python
# prism/statechart/statechart.py
async def fire(
    self,
    agent: "SocialAgent",
    trigger: str,
    context: Any = None
) -> AgentState | None:
    # For ambiguous transitions, call LLM oracle
    if needs_llm_decision:
        decision = await self._query_oracle(agent, context, options)
        return self._execute_transition(agent, decision, context)
    return self._execute_transition(agent, matched_transition, context)
```

### 4. LLM Oracle Integration

**Current Implementation:**
```python
# prism/agents/prompts.py
def build_feed_prompt(feed_text: str) -> str:
    return f"""Here is a post from your feed:
{feed_text}
What do you decide to do? Respond with JSON only."""
```

**Target Evolution:**
```python
# prism/statechart/oracle.py
def build_oracle_prompt(
    agent_name: str,
    agent_interests: list[str],
    current_state: AgentState,
    post: Post,
    options: list[AgentState]
) -> str:
    """Build prompt for LLM to decide ambiguous state transition."""
    return f"""You are {agent_name} with interests in {', '.join(agent_interests)}.
You are currently in the {current_state.value} state.

Here is a post you're evaluating:
{post.text}

Choose your next action from these options:
{format_options(options)}

Respond with JSON: {{"next_state": "..."}}"""
```

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| `SocialAgent` | ✅ | Makes decisions via LLM, no state tracking |
| `AgentDecision` | ✅ | LIKE/REPLY/RESHARE/SCROLL choices |
| `build_feed_prompt()` | ✅ | Prompt construction for decisions |
| `Post` model | ✅ | Post data for evaluation context |
| `FeedRetriever` | ✅ | Gets posts for agent to evaluate |
| `OllamaChatClient` | ✅ | LLM inference for oracle |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| `AgentState` enum | ❌ | Research doc §Proposed States |
| `Transition` dataclass | ❌ | Research doc §Minimal Core Design |
| `Statechart` class | ❌ | Research doc (~150 lines) |
| `StateTransition` history | ❌ | Track state changes for debugging |
| Oracle prompt builder | ❌ | Extends existing prompt patterns |
| Agent state field | ❌ | Add to `SocialAgent` |
| State query methods | ❌ | `agents_in_state()`, `state_distribution()` |
| Timeout transitions | ❌ | Tick-based expiry for stuck agents |

## Key Insights

### What Works Well

1. **Existing decision flow** — `SocialAgent.decide()` already calls LLM and returns structured output. The statechart wraps this flow, adding explicit state before/after.

2. **Prompt patterns** — `build_system_prompt()` and `build_feed_prompt()` provide templates for oracle prompts.

3. **Agent profile** — `SocialAgent` has `interests` and `personality` fields that map directly to statechart guard parameters.

4. **Post context** — `Post` model with engagement metrics provides rich context for transition guards (e.g., "engage if post.velocity > threshold").

5. **Async foundation** — Existing async pattern in `decide()` extends naturally to statechart oracle calls.

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| No state field on agent | Add `state: AgentState = AgentState.IDLE` to `SocialAgent` |
| No state history | Add `state_history: list[StateTransition]` for debugging/RAG |
| No global state queries | Simulation manager tracks all agents; add query methods |
| AgentDecision doesn't map to states | Map LIKE→ENGAGING_LIKE, etc. after statechart resolves |
| No tick/timeout mechanism | Statechart tracks `ticks_in_state`; timeout triggers on threshold |

### Technical Considerations

1. **Shared vs Per-Agent Statecharts**
   - **Decision**: Shared statechart definition, parameterized by agent thresholds
   - **Rationale**: One definition to maintain; agent diversity via `engagement_threshold`, `attention_span` fields
   - Research doc §Design Decisions confirms this approach

2. **Transition Execution Order**
   - Guards evaluated in definition order
   - First matching guard wins
   - SCXML semantics: "document order" for conflicting transitions

3. **LLM Oracle Scope**
   - Only for ambiguous `Evaluating → ?` transitions
   - Clear transitions (timeout, explicit triggers) don't need LLM
   - Reduces inference cost; LLM is expensive

4. **State History Depth**
   - Configurable max history length (default: 50)
   - Old entries pruned to prevent memory growth
   - History included in RAG context for "why did I do that?" reasoning

5. **Integration with Existing decide()**
   - Option A: Replace `decide()` with statechart-driven flow
   - Option B: Statechart wraps `decide()`, using it as oracle
   - **Recommendation**: Option B — minimal disruption, `decide()` becomes internal

## External References

- [W3C SCXML Specification](https://www.w3.org/TR/scxml/) — Transition semantics
- [AnyLogic Statecharts](https://anylogic.help/anylogic/statecharts/statecharts.html) — ABM patterns
- Harel, D. "Statecharts: A Visual Formalism for Complex Systems" (1987)
- Internal: `aidocs/statecharts-research.md` — detailed design rationale
