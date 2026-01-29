# Configuration Contract

## Overview

PRISM uses YAML configuration files validated by Pydantic models. The configuration drives LLM client construction without hardcoded values.

## Schema: `configs/default.yaml`

```yaml
llm:
  provider: ollama
  host: "http://localhost:11434"
  model_id: mistral
  temperature: 0.7
  max_tokens: 512
  seed: null
```

## Pydantic Model

```python
# prism/llm/config.py

from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """Configuration for the LLM client."""

    provider: Literal["ollama"] = "ollama"
    host: str = "http://localhost:11434"
    model_id: str = "mistral"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, gt=0)
    seed: int | None = None

class PrismConfig(BaseModel):
    """Root configuration for PRISM."""

    llm: LLMConfig = LLMConfig()
```

## Loading

```python
def load_config(path: str | Path = "configs/default.yaml") -> PrismConfig:
    """Load and validate PRISM configuration from YAML."""
    ...
```

## Environment Variable Overrides

The `OllamaChatClient` natively supports these environment variables as fallbacks:

| Variable | Overrides | Default |
|----------|-----------|---------|
| `OLLAMA_HOST` | `llm.host` | `http://localhost:11434` |
| `OLLAMA_MODEL_ID` | `llm.model_id` | (none) |

YAML config takes precedence when explicitly set. Environment variables serve as fallback when YAML values are not provided.

## Validation Errors

All configuration errors are raised at load time as `pydantic.ValidationError`:

- Missing required fields
- `temperature` outside [0.0, 2.0]
- `max_tokens` <= 0
- Invalid YAML syntax (raised as `yaml.YAMLError`)
- File not found (raised as `FileNotFoundError`)
