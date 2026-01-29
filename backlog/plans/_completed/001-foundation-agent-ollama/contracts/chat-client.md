# Chat Client Contract

## Overview

The LLM client layer provides a factory function that constructs an `OllamaChatClient` from validated configuration. The client is used to create `ChatAgent` instances for social agent decision-making.

## Interface: `create_llm_client`

```python
# prism/llm/client.py

from agent_framework.ollama import OllamaChatClient
from prism.llm.config import LLMConfig

def create_llm_client(config: LLMConfig) -> OllamaChatClient:
    """Create an OllamaChatClient from validated configuration.

    Args:
        config: Validated LLM configuration.

    Returns:
        Configured OllamaChatClient instance.
    """
    ...
```

## Construction Parameters

| Config Field | Maps To | Notes |
|-------------|---------|-------|
| `config.host` | `OllamaChatClient(host=...)` | Defaults to `http://localhost:11434` |
| `config.model_id` | `OllamaChatClient(model_id=...)` | Defaults to `mistral` |

## Usage Pattern

```python
config = load_config("configs/default.yaml")
client = create_llm_client(config.llm)

# Create a ChatAgent from the client
agent = await client.create_agent(
    name="agent_123",
    instructions="...",
    response_format=AgentDecision,
    temperature=config.llm.temperature,
    max_tokens=config.llm.max_tokens,
)

# Invoke the agent
response = await agent.run("feed text here")
decision = response.value  # AgentDecision instance
```

## Error Handling

- If Ollama server is unreachable, `OllamaChatClient` will raise a connection error on first use (not at construction time)
- Client construction itself does not validate connectivity
