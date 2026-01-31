# Agent Behavior Statecharts Conformance Research

**Date**: 2026-01-30
**Spec Version Reviewed**: [W3C SCXML 1.0](https://www.w3.org/TR/scxml/) (W3C Recommendation, September 2015)
**Plan Version**: plan.md (003-agent-behavior-statecharts)

## Summary

Our custom statechart implementation adopts a pragmatic subset of SCXML semantics. Full conformance is not the goal; rather, we follow SCXML where it provides clear semantics for transition selection, guard evaluation, and execution ordering. Features like parallel regions, deep history, and XML serialization are explicitly out of scope for the MVP.

## Conformance Analysis

### 1. Transition Selection

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Trigger matching | Match trigger string to transition.trigger | `<transition event="...">` matches event name | CONFORMANT |
| Source state check | `transition.source == agent.state` | Transition selected from current atomic state | CONFORMANT |
| Guard evaluation | `guard(agent, context)` callable | `cond` attribute evaluated as boolean | CONFORMANT |
| Priority (conflicts) | First matching transition wins (definition order) | Document order for same-source transitions | CONFORMANT |

**Recommendation**: None needed. Our approach matches SCXML semantics for flat state machines.

### 2. Guard Failure Handling

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Exception in guard | Not explicitly handled | "treat the expression as if it evaluated to 'false'" | UPDATE NEEDED |
| Return non-boolean | Not explicitly handled | "treat the expression as if it evaluated to 'false'" | UPDATE NEEDED |

**Recommendation**: Wrap guard evaluation in try/except, defaulting to False on any error. This is defensive and matches SCXML fail-safe semantics.

### 3. Transition Execution

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Atomicity | Single `fire()` call | "atomic and instantaneous" | CONFORMANT |
| Action execution | `action(agent, context)` called during transition | `<transition>` content executed between exit and enter | CONFORMANT |
| State update | Return new state from `fire()` | Configuration updated after transition | CONFORMANT |

**Recommendation**: None needed.

### 4. Entry/Exit Actions

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Entry actions | Not in MVP | `<onentry>` executed when entering state | FUTURE |
| Exit actions | Not in MVP | `<onexit>` executed when leaving state | FUTURE |
| Ordering | N/A | Exit innermost-first, enter outermost-first | FUTURE |

**Recommendation**: Add entry/exit action support in Phase 2 if composite states are needed. For flat states, explicit actions in transitions suffice.

### 5. Hierarchical States

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Composite states | Out of scope (MVP) | `<state>` can contain nested `<state>` | FUTURE |
| Initial substates | N/A | `initial` attribute or `<initial>` element | FUTURE |
| Transition inheritance | N/A | Transitions checked from innermost to outermost | FUTURE |

**Recommendation**: Keep states flat for MVP. The current "Engaging" substates (ENGAGING_LIKE, ENGAGING_REPLY, ENGAGING_RESHARE) are modeled as separate top-level states. This is simpler and sufficient for initial use cases.

### 6. History States

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| History pseudo-state | Out of scope | `<history>` remembers last active substate | SKIP |
| Deep history | Out of scope | `type="deep"` remembers nested substates | SKIP |

**Recommendation**: Not needed for social agent simulation. Agents don't need to "resume where they left off" after interruption.

### 7. Parallel Regions

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Concurrent states | Out of scope | `<parallel>` contains concurrent regions | SKIP |
| Synchronized transitions | N/A | Transitions can target multiple regions | SKIP |

**Recommendation**: Not needed initially. If agents need to model concurrent behaviors (e.g., "composing while monitoring notifications"), revisit.

### 8. Event Processing

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Event queue | Single trigger per `fire()` | Internal event queue with priority | SIMPLIFIED |
| Internal events | Not implemented | Actions can raise internal events | FUTURE |
| Macrosteps | Not implemented | Complete all eventless transitions before yielding | SIMPLIFIED |

**Recommendation**: Our simplified model processes one trigger per `fire()` call. This matches the simulation loop model (one event per agent per tick). Full event queuing is overkill.

### 9. Data Model

| Aspect | Plan | SCXML Spec | Status |
|--------|------|------------|--------|
| Data binding | Python objects (agent, context) | `<datamodel>` with XPath/ECMAScript | ADAPTED |
| Assignment | Direct Python mutation | `<assign>` element | ADAPTED |
| Expressions | Python lambdas for guards | XPath/ECMAScript expressions | ADAPTED |

**Recommendation**: Our Python-native approach is appropriate. SCXML's XML-based data model doesn't apply.

## New Features in Spec (Not in Plan)

| SCXML Feature | Assessment |
|---------------|------------|
| `<invoke>` | Service invocation — overkill for agent simulation |
| `<send>` | Deferred event sending — could be useful for agent-to-agent messages (FUTURE) |
| `<cancel>` | Cancel pending events — not needed without event queue |
| `<finalize>` | Process invocation results — not applicable |
| `<donedata>` | Completion data — simple done events suffice |
| `<param>` | Parameter passing — use Python arguments instead |
| `<content>` | Dynamic content — not needed |

## Recommendations

### Critical Updates

1. **Guard fail-safe** — Wrap guard evaluation in try/except, return False on error:
   ```python
   def _evaluate_guard(self, guard, agent, context):
       try:
           result = guard(agent, context)
           return bool(result)
       except Exception:
           return False
   ```

### Minor Updates

2. **Transition source validation** — Validate that all transition sources are valid states at Statechart construction time:
   ```python
   def __init__(self, states, transitions, initial):
       for t in transitions:
           if t.source not in states:
               raise ValueError(f"Invalid source state: {t.source}")
   ```

3. **Logging for debugging** — Log each transition attempt for debugging:
   ```python
   logger.debug(f"Firing trigger '{trigger}' from state '{agent.state}'")
   ```

### Future Enhancements

4. **Entry/exit actions** — Add when composite states are needed
5. **Event queue** — Add if agent-to-agent messaging requires deferred events
6. **Send/cancel** — Add for complex simulation scenarios with timed events

## Sources

- [W3C SCXML 1.0 Specification](https://www.w3.org/TR/scxml/)
- [W3C SCXML Algorithm for Interpretation](https://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation)
- [AnyLogic Statecharts Documentation](https://anylogic.help/anylogic/statecharts/statecharts.html)
- Internal: `aidocs/statecharts-research.md`

## Conclusion

The planned implementation is **substantially conformant** with SCXML semantics for flat state machines. The key gap is guard fail-safe handling, which should be added. Features like hierarchy, parallel regions, and event queues are intentionally deferred — the PRISM use case doesn't require them for MVP, and adding them would increase complexity without clear benefit.

The custom implementation approach (~150-200 lines) remains the right choice: zero external dependencies, direct LLM reasoner integration, and full control over semantics. If requirements grow significantly, migration to a library like `sismic` remains an option.
