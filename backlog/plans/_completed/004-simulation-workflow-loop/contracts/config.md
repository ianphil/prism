# Contract: SimulationConfig

## Purpose

Defines the configuration schema for simulation execution, loadable from YAML.

## Schema

```python
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class SimulationConfig(BaseModel):
    """Configuration for simulation execution."""

    max_rounds: int = Field(default=50, ge=1, description="Number of rounds to execute")
    checkpoint_frequency: int = Field(
        default=1, ge=1, description="Save checkpoint every N rounds"
    )
    checkpoint_dir: Path | None = Field(
        default=None, description="Directory for checkpoints (None = no save)"
    )
    reasoner_enabled: bool = Field(
        default=True, description="Use LLM for ambiguous state transitions"
    )
    log_decisions: bool = Field(
        default=True, description="Log decisions to structured JSON"
    )
    log_file: Path | None = Field(
        default=None, description="Path for decision log file (None = no file)"
    )

    @field_validator("checkpoint_dir", "log_file", mode="before")
    @classmethod
    def parse_path(cls, v):
        """Convert string paths to Path objects."""
        if v is None:
            return None
        return Path(v)
```

## YAML Structure

```yaml
# configs/default.yaml

simulation:
  max_rounds: 50                        # 1-10000
  checkpoint_frequency: 1               # 1 = every round
  checkpoint_dir: outputs/checkpoints   # null = no checkpoints
  reasoner_enabled: true                # false = use first valid target
  log_decisions: true                   # false = no decision logging
  log_file: outputs/decisions.jsonl     # null = no file output
```

## Loading Pattern

```python
import yaml
from prism.simulation.config import SimulationConfig

def load_config(path: Path) -> SimulationConfig:
    """Load simulation config from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return SimulationConfig(**data.get("simulation", {}))
```

## Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| max_rounds | >= 1 | Pydantic ge=1 validation |
| checkpoint_frequency | >= 1 | Pydantic ge=1 validation |
| checkpoint_dir | Valid path or None | Path.mkdir creates if needed |
| log_file | Valid path or None | Parent directory must exist |

## Usage Examples

```python
# Default configuration
config = SimulationConfig()
assert config.max_rounds == 50
assert config.reasoner_enabled is True

# Minimal test configuration
config = SimulationConfig(max_rounds=5, checkpoint_dir=None, log_file=None)

# Production configuration
config = SimulationConfig(
    max_rounds=100,
    checkpoint_frequency=10,
    checkpoint_dir=Path("outputs/checkpoints"),
    log_file=Path("outputs/decisions.jsonl"),
)
```
