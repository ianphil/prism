# Foundation: Agent Framework + Ollama — Conformance Research

**Date**: 2026-01-28
**Spec Version Reviewed**: [agent-framework 1.0.0b260127](https://pypi.org/project/agent-framework/)
**Plan Version**: plan.md

## Summary

The Microsoft Agent Framework Python SDK (beta) provides all the primitives PRISM needs: `OllamaChatClient` for local inference, `ChatAgent` for agent abstraction, structured output via Pydantic `response_format`, and async-native invocation. The API is well-documented and the Ollama integration is a first-class citizen with dedicated samples.

Key conformance finding: the PRD's conceptual code (`from agent_framework.ollama import OllamaChatClient`) matches the actual API. The `create_agent()` convenience method and `response_format` parameter both exist as documented.

## Conformance Analysis

### 1. Package Installation

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Install command | `pip install agent-framework --pre` | `pip install agent-framework --pre` (meta) or `pip install agent-framework-ollama --pre` (selective) | CONFORMANT |
| Package name | `agent-framework` | `agent-framework` (meta), `agent-framework-core` (core), `agent-framework-ollama` (selective) | UPDATE NEEDED |
| Python version | 3.11+ | >=3.10 (supports 3.10-3.14) | CONFORMANT |

**Recommendation**: Use `uv add agent-framework-ollama --pre` for minimal dependencies. This pulls in `agent-framework-core` transitively. Avoid the full `agent-framework` meta-package which includes Azure, Redis, A2A, and other unnecessary integrations.

### 2. OllamaChatClient API

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Import path | `from agent_framework.ollama import OllamaChatClient` | `from agent_framework.ollama import OllamaChatClient` | CONFORMANT |
| Constructor: endpoint | `endpoint="http://localhost:11434"` | `host="http://localhost:11434"` (or `OLLAMA_HOST` env var) | MINOR UPDATE |
| Constructor: model | `model="gpt-oss:20b"` | `model_id="gpt-oss:20b"` (or `OLLAMA_MODEL_ID` env var) | MINOR UPDATE |
| Env var support | Not mentioned | `OLLAMA_HOST`, `OLLAMA_MODEL_ID`, `.env` file support | CONFORMANT (bonus) |

**Recommendation**: Use `host` instead of `endpoint`, `model_id` instead of `model`. Support env vars as an alternative to YAML config.

### 3. ChatAgent Creation

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Creation pattern | `ChatAgent(chat_client=client, name=..., instructions=...)` | `ChatAgent(chat_client=client, name=..., instructions=...)` or `client.create_agent(name=..., instructions=...)` | CONFORMANT |
| Convenience method | Not mentioned | `client.create_agent()` with full parameter support | CONFORMANT (bonus) |
| Parameters | `name`, `instructions` | `name`, `instructions`, `temperature`, `seed`, `max_tokens`, `response_format`, `tools`, `tool_choice`, and more | CONFORMANT |

**Recommendation**: Use `client.create_agent()` convenience method for cleaner code. It wires the client automatically and exposes all inference parameters.

### 4. Agent Invocation

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Invocation | Not specified | `await agent.run(message)` returns response | UPDATE NEEDED |
| Streaming | Not specified | `async for update in agent.run_stream(message)` | CONFORMANT |
| Response access | Not specified | `response.text` (string), `response.value` (structured) | UPDATE NEEDED |

**Recommendation**: Use `await agent.run(feed_text)` for decisions. Access structured output via `response.value`.

### 5. Structured Output

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Output format | "Choice-Reason-Content triplets" | `response_format=BaseModel` on `create_agent()` or `run()` | CONFORMANT |
| Access pattern | Not specified | `response.value` returns Pydantic instance | UPDATE NEEDED |
| Model support | gpt-oss:20b | Depends on model; may need prompt-based fallback for some Ollama models | RISK |

**Recommendation**: Define `AgentDecision(BaseModel)` with `choice`, `reason`, `content`. Pass as `response_format` to `agent.run()`. Implement prompt-based JSON fallback for models that don't support native structured output.

### 6. Configuration

| Aspect | Plan (PRD) | Actual SDK | Status |
|--------|------------|------------|--------|
| Config approach | YAML files | SDK supports env vars and `.env` files natively | CONFORMANT |
| Model selection | Config-driven | `model_id` param + `OLLAMA_MODEL_ID` env var | CONFORMANT |

**Recommendation**: Use YAML config as primary (loaded by PRISM), with env var fallback (supported natively by `OllamaChatClient`).

## New Features in Spec (Not in Plan)

1. **`create_agent()` convenience method**: Simplifies agent creation by combining client + agent setup. Not in original quick plan but should be used.
2. **`.env` file support**: `OllamaChatClient` natively supports `env_file_path` parameter. Useful for local dev.
3. **`from_dict()` / `from_json()` class methods**: Could enable config-driven client construction without manual parameter mapping.
4. **`conversation_id` parameter**: Supports multi-turn conversations. Not needed for MVP but useful for future agent memory.
5. **`context_providers` parameter**: Extensibility hook for injecting context. Not needed now but maps to future RAG integration.

## Recommendations

### Critical Updates

1. **Use `host` not `endpoint`** — The `OllamaChatClient` constructor uses `host`, not `endpoint`. Update all references.
2. **Use `model_id` not `model`** — The constructor parameter is `model_id`. Update all references.
3. **Use `uv add` not `pip install`** — Per CLAUDE.md, all dependency management must use `uv`. Use `uv add agent-framework-ollama --pre`.

### Minor Updates

4. **Use `client.create_agent()` convenience method** — Cleaner than manually constructing `ChatAgent(chat_client=...)`.
5. **Support env var fallback** — `OLLAMA_HOST` and `OLLAMA_MODEL_ID` are supported natively; document as alternative to YAML.
6. **Handle structured output gracefully** — Not all Ollama models support `response_format`. Implement JSON-in-prompt fallback.

### Future Enhancements

7. **`from_dict()` for config-driven construction** — Could simplify YAML → client mapping.
8. **`context_providers` for RAG** — Feature 2 can inject feed context via this mechanism.
9. **`conversation_id` for memory** — Multi-round agent memory across simulation rounds.

## Sources

- [Agent Framework PyPI](https://pypi.org/project/agent-framework/)
- [ChatClientAgent Docs](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/chat-client-agent)
- [OllamaChatClient API Reference](https://learn.microsoft.com/es-es/python/api/agent-framework-core/agent_framework.ollama.ollamachatclient?view=agent-framework-python-latest)
- [Ollama Samples (GitHub)](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents/ollama)
- [Structured Output Tutorial](https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output)
- [Run Agent Tutorial](https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent)

## Conclusion

The Microsoft Agent Framework Python SDK closely matches the PRD's conceptual design. The main corrections are parameter naming (`host`/`model_id` vs `endpoint`/`model`), package installation (`uv add agent-framework-ollama --pre`), and adding the `response_format` invocation pattern. The framework provides more than needed for MVP, with clear extension points for future features.
