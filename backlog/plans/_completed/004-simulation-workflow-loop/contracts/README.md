# Simulation Workflow Loop Contracts

Interface definitions for the simulation orchestration layer.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [config.md](config.md) | SimulationConfig schema and YAML structure |
| [state.md](state.md) | SimulationState and related dataclasses |
| [executor.md](executor.md) | Executor protocol and pipeline interfaces |
| [checkpointer.md](checkpointer.md) | Checkpoint serialization format |

## Contract Principles

- All configuration is validated via Pydantic models
- Executors follow a consistent async interface
- Checkpoints use JSON with explicit version field
- State mutation is explicit (no hidden side effects)
