---
title: "Agent Behavior Statecharts"
status: open
priority: high
created: 2026-01-30
depends_on: ["001-foundation-agent-ollama"]
---

# Agent Behavior Statecharts

## Summary

Implement Harel-style statecharts to model agent behavioral states and transitions, providing inspectable, debuggable agent decision-making that integrates with the LLM reasoning engine.

## Motivation

Current agent design treats decisions as stateless LLM calls each round. This makes it difficult to:
- Understand *why* cascades form (agent state is implicit in LLM reasoning)
- Debug agent behavior at scale (no queryable state)
- Model realistic behavioral patterns (humans have modes: lurking, engaging, creating)

Statecharts give agents explicit behavioral states with governed transitions, while the LLM remains the "oracle" for deciding *which* transition to take.

## Proposal

### Goals

- Define agent behavioral states (Idle, Scrolling, Evaluating, Composing, Engaging)
- Implement state transitions triggered by events (sees_post, decides_engage, timeout, rate)
- Use LLM inference as the decision oracle for non-deterministic transitions
- Enable state queries ("how many agents in Composing state?")
- Support hierarchical states for complex behaviors (e.g., Engaging → {Replying, Resharing, Liking})

### Non-Goals

- Visual statechart editor (use code definitions)
- Parallel/concurrent state regions (keep initial implementation simple)
- Full UML statechart compliance (pragmatic subset)

## Design

Agent behavior modeled as a statechart where:

1. **States** represent behavioral modes with entry/exit actions
2. **Transitions** have triggers (event, timeout, condition) and optional guards
3. **LLM Oracle**: For transitions like `Evaluating → ?`, the LLM decides the target state based on post content and agent personality
4. **State History**: Track state transitions for observability and cascade analysis

```
[Idle] ──feed_ready──▶ [Scrolling] ──sees_post──▶ [Evaluating]
                            │                          │
                            │                     ┌────┴────┐
                        timeout                   │         │
                            │              decides_ignore  decides_engage
                            ▼                     │         │
                         [Idle]                   ▼         ▼
                                            [Scrolling] [Composing]
                                                            │
                                                      ──────┴──────
                                                      │     │     │
                                                   Reply Reshare Like
```

Implementation approach:
- `Statechart` class with state registry and transition definitions
- `AgentState` enum or class hierarchy for states
- `Transition` with trigger type, guard condition, and action
- Integration point: `SocialAgent.decide()` consults statechart, uses LLM for ambiguous transitions

## Tasks

- [ ] Define `AgentState` enum (Idle, Scrolling, Evaluating, Composing, Engaging substates)
- [ ] Implement `Transition` dataclass (trigger, source, target, guard, action)
- [ ] Implement `Statechart` class (~150 lines: states, transitions, fire, valid_triggers)
- [ ] Add timeout transition support (tick-based expiry)
- [ ] Add LLM oracle integration for ambiguous transitions
- [ ] Integrate statechart into `SocialAgent.decide()` flow
- [ ] Add state query methods (agents_in_state, state_distribution)
- [ ] Write tests for state transitions, guards, and timeouts

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Statechart scope | Shared + parameterized | One statechart definition; behavior varies via agent thresholds/weights. Simpler to maintain, can evolve to hybrid later if needed. |
| Stuck agents | Timeout transitions | Auto-transition to Idle/Scrolling after N ticks of simulation time. Prevents deadlocks. |
| State history | Agent memory | Each agent tracks its own state history, included in RAG context for LLM decisions. Enables "why did I reshare that?" reasoning. |
| Implementation | Custom (~150 lines) | No external library. Zero deps, tight LLM oracle integration, full control. Core is simple; add hierarchy/history only if needed. |
