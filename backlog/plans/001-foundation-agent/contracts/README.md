# Foundation Agent Contracts

Interface definitions for the foundation agent framework.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [llm-client.md](llm-client.md) | LLM client interface specification |
| [agent-decision.md](agent-decision.md) | Decision output schema |

## Contract Principles

- All public interfaces are type-annotated
- Async/await for all I/O operations
- Pydantic for validation where appropriate
- Dataclasses for simple data structures

## LLM Client Interface

```python
from typing import Protocol
from prism.llm.config import LLMConfig

class IChatClient(Protocol):
    """Interface for LLM chat clients."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": str}
            **kwargs: Additional model-specific parameters

        Returns:
            The model's response text

        Raises:
            TimeoutError: If request times out
            ConnectionError: If LLM service unavailable
        """
        ...
```

## Agent Interface

```python
from typing import Protocol
from prism.agents.decisions import AgentDecision
from prism.models.post import Post

class IAgent(Protocol):
    """Interface for social media agents."""

    async def decide(self, feed: list[Post]) -> AgentDecision:
        """
        Make a decision about how to interact with the feed.

        Args:
            feed: List of posts to evaluate

        Returns:
            AgentDecision with choice, reason, and optional content
        """
        ...
```

## Configuration Schema

See `configs/default.yaml` for the configuration file format:

```yaml
llm:
  endpoint: string      # Ollama API URL
  model: string         # Model name
  reasoning_effort: string  # low|medium|high
  timeout: integer      # Seconds
  temperature: float    # 0.0-2.0

agent:
  default_personality: string

logging:
  level: string  # DEBUG|INFO|WARNING|ERROR
```
