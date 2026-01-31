# Simulation Workflow Loop Conformance Research

**Date**: 2026-01-30
**Spec Version Reviewed**: [PRD v1.2](../../aidocs/prd.md)
**Plan Version**: plan.md

## Summary

This feature implements the core simulation loop described in PRD §4.2 "Simulation Orchestration". The plan is substantially conformant with the PRD vision, with some simplifications for MVP that preserve extensibility for future phases.

## Conformance Analysis

### 1. Workflow Architecture

| Aspect | Plan | PRD | Status |
|--------|------|-----|--------|
| Graph-based workflow | Sequential pipeline (executors) | Agent Framework Workflow class | SIMPLIFIED |
| Executor sequence | feed → decision → state → logging | feed → decision → state → logging | CONFORMANT |
| Checkpointing | JSON per round | "checkpointing and replay" | CONFORMANT |
| Parallelism | Sequential MVP, parallel future | "configurable parallelism" | PARTIAL |

**Recommendation**: The PRD shows conceptual code using `Workflow` and `Edge` classes from Agent Framework. Our implementation uses a simpler sequential pipeline without external dependencies. This is acceptable for MVP - the Agent Framework workflow abstractions add complexity without benefit at this scale. If we later need distributed execution, we can wrap our executors in Agent Framework primitives.

### 2. Statechart Integration

| Aspect | Plan | PRD Quick Plan | Status |
|--------|------|----------------|--------|
| Statechart.fire() | Core decision mechanism | "Replaces direct decide() calls" | CONFORMANT |
| agent.tick() | Called each round | "Called each round to track time-in-state" | CONFORMANT |
| is_timed_out() | Checked before firing | "Checked before firing" | CONFORMANT |
| Reasoner | Invoked for ambiguous transitions | "Invoked when multiple transitions valid" | CONFORMANT |
| transition_to() | Records state change | "Records state change + history" | CONFORMANT |
| state_distribution() | Logged per round | "Query for observability each round" | CONFORMANT |

**Recommendation**: Statechart integration matches the Feature 003 design exactly. No changes needed.

### 3. State Management

| Aspect | Plan | PRD | Status |
|--------|------|-----|--------|
| Posts collection | list[Post] in SimulationState | "Posts storage" | CONFORMANT |
| Engagement metrics | EngagementMetrics dataclass | "Engagement metrics evolve" | CONFORMANT |
| Agent state | Via SocialAgent.state | "Agent action history" | CONFORMANT |
| Round tracking | round_number field | "Round-robin iterations" | CONFORMANT |

**Recommendation**: State management covers all PRD requirements. The `EngagementMetrics` aggregation (total likes, reshares, replies) is our extension for easier analysis.

### 4. Feed Retrieval

| Aspect | Plan | PRD | Status |
|--------|------|-----|--------|
| RAG query | FeedRetriever.get_feed() | "Queries RAG system for each agent's feed" | CONFORMANT |
| Preference mode | Via existing FeedRetriever | "Preference-based" | CONFORMANT |
| Random mode | Via existing FeedRetriever | "Random sampling" | CONFORMANT |
| X algo integration | Out of scope (Feature 005) | "X algo scoring" | DEFERRED |

**Recommendation**: Feed retrieval wraps existing Feature 002 components. X algorithm ranking is correctly deferred to Feature 005.

### 5. Round Controller

| Aspect | Plan | PRD | Status |
|--------|------|-----|--------|
| Round count | Configurable max_rounds | "50-100 rounds" | CONFORMANT |
| Agent count | Configurable via agent list | "250-500 agents" | CONFORMANT |
| Turn order | Sequential (all agents per round) | "round-robin" | CONFORMANT |
| Agent batching | Future enhancement | "configurable parallelism" | DEFERRED |

**Recommendation**: Sequential processing is acceptable for MVP. The PRD estimates ~5 hours for 500 agents × 50 rounds with 4x parallel - sequential will be slower but simpler to debug.

### 6. Logging and Observability

| Aspect | Plan | PRD | Status |
|--------|------|-----|--------|
| Decision logging | Structured JSON per decision | "Logging (metrics, traces)" | CONFORMANT |
| State transitions | Logged in JSON | "Record decisions and state transitions" | CONFORMANT |
| OpenTelemetry | Out of scope (Feature 006) | "OpenTelemetry integration" | DEFERRED |

**Recommendation**: We implement structured logging but defer OpenTelemetry tracing to Feature 006 as designed.

## New Features in Spec (Not in Plan)

### From PRD that we're deferring:

1. **Agent Framework Workflow class** - Using simple sequential pipeline instead. Acceptable for MVP.

2. **Parallel Ollama instances** - PRD mentions 2-4 parallel model instances. We support only sequential for now.

3. **Time-travel debugging** - PRD mentions this as a goal. Checkpointing enables replay, which is the foundation for time-travel.

4. **Cascade tracking** - PRD mentions NetworkX for cascade analysis. Not included in simulation loop - this is post-simulation analysis.

## Recommendations

### Critical Updates

None required. The plan is substantially conformant with PRD requirements.

### Minor Updates

1. **Add turn order configuration** - While we implement sequential round-robin, consider adding config option for shuffle vs. fixed order. This affects reproducibility.

2. **Checkpoint compression** - For 500-agent simulations, JSON may grow large. Consider gzip compression on write.

### Future Enhancements

1. **Parallel agent processing** - Use asyncio.gather() with semaphore for controlled parallelism.

2. **Streaming checkpoints** - Write incrementally rather than full state dump.

3. **Agent Framework workflow wrapper** - If we need distributed execution, wrap executors in AF primitives.

## Sources

- [PRISM PRD v1.2](../../aidocs/prd.md) - Primary requirements document
- [Feature 003 Plan](../_completed/003-agent-behavior-statecharts/plan.md) - Statechart integration points
- [Quick Plan](../20260127-simulation-workflow-loop.md) - Initial feature sketch

## Conclusion

The simulation workflow loop plan is well-aligned with PRD requirements. Key simplifications (sequential vs. parallel, simple pipeline vs. workflow library) are appropriate for MVP while preserving extensibility. The statechart integration follows the Feature 003 design exactly. Checkpointing and logging provide the observability foundation for future OpenTelemetry integration.

No critical changes required. Proceed to implementation.
