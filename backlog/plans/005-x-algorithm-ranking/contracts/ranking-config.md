# RankingConfig Contract

## Overview

Configuration model for X algorithm ranking parameters. Extends the RAG configuration with ranking-specific settings.

## Schema

```python
from typing import Literal
from pydantic import BaseModel, Field, model_validator

RankingMode = Literal["x_algo", "preference", "random"]

class RankingConfig(BaseModel):
    """Configuration for X algorithm ranking."""

    mode: RankingMode = "preference"

    # Scale factors (from X's RescoringFactorProvider)
    out_of_network_scale: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Multiplicative penalty for out-of-network posts"
    )
    reply_scale: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Multiplicative penalty for reply posts"
    )

    # Author diversity (from X's AuthorDiversityDecayFactor)
    author_diversity_decay: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Exponential decay factor per author occurrence"
    )
    author_diversity_floor: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum score after author diversity decay"
    )

    # Candidate limits
    in_network_limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum in-network candidates to consider"
    )
    out_of_network_limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum out-of-network candidates to consider"
    )

    @model_validator(mode="after")
    def validate_floor_less_than_decay(self) -> "RankingConfig":
        """Ensure floor doesn't exceed decay factor."""
        if self.author_diversity_floor > self.author_diversity_decay:
            raise ValueError(
                f"author_diversity_floor ({self.author_diversity_floor}) "
                f"must be <= author_diversity_decay ({self.author_diversity_decay})"
            )
        return self
```

## YAML Configuration

```yaml
ranking:
  mode: x_algo
  out_of_network_scale: 0.75
  reply_scale: 0.75
  author_diversity_decay: 0.5
  author_diversity_floor: 0.25
  in_network_limit: 50
  out_of_network_limit: 50
```

## Integration with RAGConfig

```python
class RAGConfig(BaseModel):
    # ... existing fields ...
    ranking: RankingConfig = Field(default_factory=RankingConfig)
```

## Mode Behavior

| Mode | Behavior |
|------|----------|
| `x_algo` | Full ranking pipeline with INN/OON, scale factors, author diversity |
| `preference` | Similarity-based ranking only (existing behavior) |
| `random` | Uniform random sampling (existing behavior) |

## Validation Rules

1. All scale factors in [0.0, 1.0]
2. `author_diversity_floor` <= `author_diversity_decay`
3. Limits >= 1 and <= 500
4. Mode must be one of the allowed literals
