# Foundation Agent Framework Contracts

Interface definitions for the foundation agent layer.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [chat-client.md](chat-client.md) | LLM client construction and invocation protocol |
| [agent-decision.md](agent-decision.md) | Agent decision schema and validation rules |
| [config.md](config.md) | Configuration schema for LLM settings |

## Contract Principles

- All public interfaces are type-annotated
- Configuration is validated at load time, not at use time
- Agent decisions are always `AgentDecision` Pydantic models, never raw dicts
- LLM client is injected, never hardcoded — enables testing with mocks
- All agent operations are async
