# Statecharts for Agent Behavior Modeling

Research notes on using Harel statecharts to model agent behavioral states in PRISM.

## Background

Statecharts were introduced by David Harel in the 1980s as an extension to finite state machines (FSMs) for modeling complex reactive systems. His work won the Stevens Award in Software Development Methods (1996) and the Israel Prime Minister's Prize for Software (1997).

The key insight: traditional FSMs become unwieldy for complex behaviors due to state explosion. Statecharts add hierarchy, concurrency, and memory to make complex behavior manageable.

## Core Concepts

### States and Transitions

A **state** represents a behavioral mode — a "concentrated history" of the agent that determines its future reactions. Instead of tracking every variable, meaningful behavioral modes are captured.

A **transition** is an atomic, instantaneous change between states. When triggered, the agent moves to a new state with a new set of possible reactions.

### Triggers

Transitions can be triggered by:

| Trigger Type | Description | PRISM Example |
|--------------|-------------|---------------|
| **Event/Message** | External signal received | `sees_post`, `receives_reply` |
| **Timeout** | Elapsed time in state | After 5 simulation ticks in `Evaluating` |
| **Rate** | Probabilistic firing | 10% chance per tick to lose interest |
| **Condition** | Boolean guard becomes true | `post.relevance > agent.threshold` |

### Hierarchical (Composite) States

States can contain substates. A composite state groups behaviors with common characteristics:

```
[Engaging]
    ├── [Replying]
    ├── [Resharing]
    └── [Liking]
```

Benefits:
- Common exit transitions (e.g., "distracted" exits any Engaging substate)
- Cleaner diagrams — hide substate complexity when zoomed out
- Reusable behavioral patterns

### History States

A history state remembers which substate was active when leaving a composite state. Enables "resume where you left off" behavior.

Example: Agent is `Composing → Drafting`, gets interrupted, goes to `Idle`. When returning to `Composing`, history state resumes at `Drafting` rather than starting over.

### Guards

Boolean conditions that must be true for a transition to fire. Allow the same trigger to lead to different states based on context:

```
[Evaluating] --decides_engage--> [Composing]    guard: post.relevance > 0.7
[Evaluating] --decides_engage--> [Liking]       guard: post.relevance > 0.3
[Evaluating] --decides_engage--> [Scrolling]    guard: otherwise
```

## Application in Agent-Based Modeling

### AnyLogic Approach

AnyLogic (a leading ABM platform) uses UML statecharts as the primary mechanism for agent behavior:

> "A statechart defines the current status of an agent... Each type of agent can have its own statechart and behavior."

Key patterns from AnyLogic:
- Each agent type has a statechart defining its behavioral repertoire
- States like `Developing`, `AnsweringQuestions`, `Communicating` for developer agents
- Transitions triggered by messages between agents
- Statecharts enable visual debugging — see agent state distribution at any simulation step

### Why Statecharts for Social Media Agents

Current PRISM design: Agents make decisions via stateless LLM calls each round. The LLM's "state" is implicit in its reasoning.

Problems this creates:
1. **Opaque behavior** — Can't query "how many agents are composing right now?"
2. **No behavioral momentum** — Agent evaluates each post independently, no "I'm on a liking spree" state
3. **Debugging difficulty** — Why did this cascade form? Hard to trace without explicit state

Statecharts provide:
- **Inspectable state** — Query agent state distribution at any round
- **Behavioral modes** — Agent in `Lurking` state behaves differently than `Engaging`
- **Traceable transitions** — Log every state change for cascade analysis
- **LLM as oracle** — Statechart governs flow, LLM decides ambiguous transitions

## Proposed PRISM Agent Statechart

```
                              ┌─────────────────────────────────────┐
                              │            [Active]                 │
                              │                                     │
    ┌───────┐  feed_ready     │  ┌──────────┐    sees_post          │
    │ Idle  │────────────────▶│  │ Scrolling │──────────────┐       │
    └───────┘                 │  └──────────┘               │       │
        ▲                     │       │                     ▼       │
        │                     │       │ timeout      ┌────────────┐ │
        │                     │       │              │ Evaluating │ │
        │                     │       ▼              └────────────┘ │
        │                     │  ┌──────────┐            │         │
        │    round_ends       │  │ Resting  │      ┌─────┴─────┐   │
        └─────────────────────│  └──────────┘      │           │   │
                              │                 ignores    decides  │
                              │                    │      engage   │
                              │                    ▼           │   │
                              │              [Scrolling]       │   │
                              │                                │   │
                              │                    ┌───────────┘   │
                              │                    ▼               │
                              │             ┌────────────┐         │
                              │             │ Composing  │         │
                              │             └────────────┘         │
                              │                    │               │
                              │              posts/replies         │
                              │                    │               │
                              │                    ▼               │
                              │             ┌────────────┐         │
                              │             │ [Engaging] │         │
                              │             │  ├─Reply   │         │
                              │             │  ├─Reshare │         │
                              │             │  └─Like    │         │
                              │             └────────────┘         │
                              │                                     │
                              └─────────────────────────────────────┘
```

### State Descriptions

| State | Description | Entry Action | Exit Action |
|-------|-------------|--------------|-------------|
| `Idle` | Not actively browsing | — | — |
| `Scrolling` | Browsing feed, not focused on any post | Request next feed batch | — |
| `Evaluating` | Considering a specific post | Record post impression | — |
| `Composing` | Drafting content (reply or original) | — | — |
| `Engaging` | Taking action on post | — | Update engagement metrics |
| `Resting` | Cooling down after activity | — | — |

### Transition Guards (Parameterized)

```python
# Shared statechart, behavior varies via agent parameters
transitions = [
    Transition(
        from_state="Evaluating",
        to_state="Composing",
        trigger="decides_engage",
        guard=lambda agent, post: post.relevance_score > agent.engagement_threshold
    ),
    Transition(
        from_state="Scrolling",
        to_state="Idle",
        trigger="timeout",
        guard=lambda agent, _: agent.attention_span_expired()
    ),
]

# Agent archetypes via parameter tuning
lurker = Agent(engagement_threshold=0.95, attention_span=3)
influencer = Agent(engagement_threshold=0.3, attention_span=20)
```

### LLM-based Agent Reasoner

For non-deterministic transitions (e.g., `Evaluating → ?`), the LLM decides:

```python
def decide_transition(agent, post, possible_transitions):
    """LLM picks which transition to take."""
    prompt = f"""
    You are {agent.name} with interests in {agent.interests}.
    You're evaluating this post: {post.text}

    Options:
    1. IGNORE - Keep scrolling
    2. LIKE - Quick appreciation
    3. RESHARE - Amplify to followers
    4. REPLY - Engage in conversation

    What do you do?
    """
    decision = llm.complete(prompt)
    return map_decision_to_transition(decision)
```

## Design Decisions for PRISM

Based on analysis, the following decisions were made:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Statechart scope | Shared + parameterized | One definition, behavior varies via agent thresholds. Simpler to maintain. |
| Stuck agents | Timeout transitions | Auto-transition to Idle after N ticks prevents deadlocks. |
| State history | Agent memory | Stored in agent for RAG context. Enables "why did I reshare that?" reasoning. |
| Parallel regions | Not initially | Keep simple; add if needed for modeling concurrent behaviors. |

## Implementation Approach

**Decision: Custom implementation** (no external library)

Rationale:
- Core statechart logic is ~150-200 lines of Python
- Zero external dependencies
- Direct LLM oracle integration without adapter layers
- Full control over semantics and debugging
- Features we don't need (parallel regions, deep history) add library complexity

### Minimal Core Design

```python
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Transition:
    trigger: str
    source: str
    target: str
    guard: Callable[[Agent, Any], bool] | None = None
    action: Callable[[Agent, Any], None] | None = None

class Statechart:
    def __init__(self, states: list[str], transitions: list[Transition], initial: str):
        self.states = set(states)
        self.transitions = transitions
        self.initial = initial

    def fire(self, agent: Agent, trigger: str, context: Any = None) -> str | None:
        """Attempt transition, return new state or None if no valid transition."""
        for t in self.transitions:
            if t.source == agent.state and t.trigger == trigger:
                if t.guard is None or t.guard(agent, context):
                    if t.action:
                        t.action(agent, context)
                    return t.target
        return None

    def valid_triggers(self, state: str) -> list[str]:
        """Return triggers available from given state."""
        return [t.trigger for t in self.transitions if t.source == state]
```

### Extension Points

Add these only if needed:
- **Hierarchical states**: Composite state class with enter/exit actions
- **History states**: Store last active substate per composite
- **Timeout transitions**: Timer-based trigger checked each simulation tick

Libraries like `transitions` or `sismic` remain fallback options if requirements grow beyond custom implementation.

## W3C SCXML Specification

The [W3C SCXML (State Chart XML)](https://www.w3.org/TR/scxml/) spec is the formal standard for statechart semantics (W3C Recommendation, September 2015). While we're not using XML, the spec defines execution semantics worth following.

### Semantics We Adopt

**Transition Selection Priority**:
> "If no transitions match in the atomic state, the state machine will look in its parent state, then in the parent's parent, etc."

For conflicting transitions: innermost state wins, then document order. Important if we add hierarchical states.

**Entry/Exit Ordering**:
- Exit handlers execute innermost-first (leaf → root)
- Transition content executes
- Entry handlers execute outermost-first (root → leaf)

**Guard Fail-Safe**:
> "If a conditional expression cannot be evaluated as a boolean value... the SCXML Processor MUST treat the expression as if it evaluated to 'false'."

Defensive behavior — malformed guards don't crash, they just don't fire.

**Event Processing**:
- Events queue internally
- Internal events (from actions) process before external events
- State machine completes all entry handlers before processing next event

This matters for LLM oracle: if `decide_engage` triggers `compose_started`, that internal event processes immediately.

**Microsteps and Macrosteps**:
Transitions execute in microsteps (exit → content → enter). Eventless transitions can chain into multiple microsteps before yielding. A macrostep completes when no more eventless transitions are enabled.

### Semantics We Skip

| SCXML Feature | Why Skip |
|---------------|----------|
| `<parallel>` regions | Not needed initially; adds complexity |
| LCCA (Least Common Compound Ancestor) | Only matters with deep nesting |
| `<invoke>`, `<send>`, `<cancel>` | Overkill for agent-to-agent communication |
| XPath/ECMAScript data models | We use Python directly |
| `<donedata>` completion data | Simple done events suffice |

### Useful Pseudo-code from Spec

The spec includes [Algorithm for SCXML Interpretation](https://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation) with detailed pseudo-code for:
- `selectTransitions(event)` — finds enabled transitions
- `microstep(enabledTransitions)` — executes one transition set
- `exitStates(enabledTransitions)` — determines exit order
- `enterStates(enabledTransitions)` — determines entry order

Reference these if implementing hierarchical states later.

## References

- [W3C SCXML Specification](https://www.w3.org/TR/scxml/) — Formal statechart semantics (W3C Recommendation 2015)
- [AnyLogic Statecharts Documentation](https://anylogic.help/anylogic/statecharts/statecharts.html)
- [AnyLogic Statecharts Chapter (PDF)](https://www.anylogic.com/upload/books/new-big-book/7-statecharts.pdf)
- Harel, D. "Statecharts: A Visual Formalism for Complex Systems" (1987)
- Harel, D. & Politi, M. "Modeling Reactive Systems With Statecharts" (1998)

## Next Steps

1. Expand with `/planner` for full TDD task breakdown
2. Evaluate `transitions` library with prototype
3. Define complete state/transition schema for social agents
4. Integrate with existing `SocialAgent` class from Feature 1
