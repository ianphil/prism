# Agent Behavior Statecharts Contracts

Interface definitions for the statechart system.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [statechart.md](statechart.md) | Core statechart interfaces (Statechart, Transition) |
| [reasoner.md](reasoner.md) | LLM-based Agent Reasoner for ambiguous transitions |
| [agent-state.md](agent-state.md) | Agent state management extensions |

## Contract Principles

1. **Immutability** — Statechart and Transition definitions are immutable after construction
2. **Fail-safe guards** — Guard exceptions return False, not crash
3. **Explicit reasoning** — Reasoner invoked only for explicitly ambiguous cases
4. **History bounded** — State history has configurable max depth with FIFO pruning
5. **JSON-serializable** — All state types serialize to JSON for logging/debugging
