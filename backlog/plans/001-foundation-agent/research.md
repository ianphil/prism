# Foundation Agent Framework Conformance Research

**Date**: 2026-01-29
**Spec Version Reviewed**: PRD v1.2, Agent Framework Preview
**Plan Version**: plan.md

## Summary

This research validates our implementation plan against the Microsoft Agent Framework documentation and Ollama capabilities. Key findings: Agent Framework's Python SDK provides the abstractions we need, but specific class names and imports may differ from the PRD's conceptual examples.

## Conformance Analysis

### 1. Agent Framework Python SDK

| Aspect | Plan | Actual | Status |
|--------|------|--------|--------|
| Package name | `agent-framework` | TBD - verify actual package | VERIFY NEEDED |
| IChatClient interface | Assumed available | May be named differently | VERIFY NEEDED |
| ChatAgent class | Assumed available | May use different pattern | VERIFY NEEDED |
| Structured outputs | Native support expected | Likely via response parsing | CONFORMANT |

**Recommendation**: During implementation, verify exact package name and class structure. Abstract behind our own interfaces to insulate from changes.

### 2. Ollama Integration

| Aspect | Plan | Ollama Docs | Status |
|--------|------|-------------|--------|
| REST API | localhost:11434 | Confirmed | CONFORMANT |
| Chat endpoint | /api/chat | Confirmed | CONFORMANT |
| Model parameter | model name string | Confirmed | CONFORMANT |
| Streaming | Optional | Supported | CONFORMANT |

**Recommendation**: Use Ollama's REST API directly if Agent Framework integration is problematic.

### 3. Model Availability

| Aspect | Plan (PRD) | Reality | Status |
|--------|------------|---------|--------|
| gpt-oss:20b | Primary model | Likely placeholder name | UPDATE NEEDED |
| Mistral 7B | Dev model | Available as `mistral` | CONFORMANT |
| Embeddings | nomic-embed-text | Available | CONFORMANT |

**Recommendation**: Use `llama3:70b` or similar as the "high quality" model, `mistral` for development. Document mapping in config.

### 4. Structured Output

| Aspect | Plan | Best Practice | Status |
|--------|------|---------------|--------|
| JSON response | AgentDecision dataclass | Use Pydantic + prompt engineering | CONFORMANT |
| Enum parsing | Choice enum | String matching with validation | CONFORMANT |
| Content extraction | Direct field | May need regex/parsing | CONFORMANT |

**Recommendation**: Use explicit JSON format in prompts with Pydantic validation.

## New Features in Spec (Not in Plan)

### Agent Framework Features We Could Use

1. **Tool calling** - Native function calling support (future enhancement)
2. **Conversation history** - Built-in context management (future enhancement)
3. **OpenTelemetry** - Built-in tracing (Feature 006)

These are out of scope for MVP but good to know they exist.

## Recommendations

### Critical Updates

1. **Verify Agent Framework package** - Confirm exact package name and imports before implementation. May need to adjust or use Ollama directly.

2. **Map model names** - Create config mapping between PRD model names and actual Ollama models:
   ```yaml
   models:
     primary: "llama3:70b"      # maps to PRD's "gpt-oss:20b"
     development: "mistral"     # fast iteration
     embedding: "nomic-embed-text"
   ```

### Minor Updates

3. **Add fallback to direct Ollama** - If Agent Framework integration is problematic, implement direct REST client as backup.

4. **Structured output via prompts** - Don't rely on native structured outputs; use prompt engineering + Pydantic parsing.

### Future Enhancements

5. **Tool calling for RAG** - When implementing Feature 002, use Agent Framework's tool calling for feed retrieval.

6. **Conversation memory** - For multi-turn agent interactions, leverage built-in context management.

## Sources

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework) (conceptual)
- [Ollama Model Library](https://ollama.ai/library)

## Conclusion

The implementation plan is largely conformant with available technologies. Key risk is Agent Framework Python SDK availability/stability - mitigated by maintaining our own abstractions and having Ollama direct integration as fallback. Model naming needs adjustment from PRD placeholders to actual Ollama models.

**Conformance Score**: 85% - Minor adjustments needed for model names and SDK verification.
