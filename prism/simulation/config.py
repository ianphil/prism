"""Configuration models for simulation workflow.

This module defines the SimulationConfig Pydantic model that provides
configuration for simulation execution including max rounds, checkpointing,
and logging settings.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class SimulationConfig(BaseModel):
    """Configuration for simulation execution.

    Attributes:
        max_rounds: Maximum number of simulation rounds to run (must be >= 1).
        checkpoint_frequency: How often to save checkpoints (must be >= 1).
        checkpoint_dir: Directory for checkpoint files (None to disable).
        reasoner_enabled: Whether to use LLM reasoner for ambiguous transitions.
        log_decisions: Whether to log decisions to structured JSON.
        log_file: File for structured logging output (None to disable).
    """

    max_rounds: int = Field(default=50, ge=1)
    checkpoint_frequency: int = Field(default=5, ge=1)
    checkpoint_dir: Path | None = None
    reasoner_enabled: bool = Field(default=True)
    log_decisions: bool = Field(default=True)
    log_file: Path | None = None

    @field_validator("checkpoint_dir", "log_file", mode="before")
    @classmethod
    def parse_path(cls, v: Any) -> Path | None:
        """Convert string paths to Path objects.

        Args:
            v: Value to parse (string, Path, or None).

        Returns:
            Path object or None.
        """
        if v is None:
            return None
        return Path(v)


def load_config(path: Path) -> SimulationConfig:
    """Load simulation configuration from a YAML file.

    Reads the 'simulation' section from the YAML file and creates
    a SimulationConfig. If the section is missing, default values
    are used.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        SimulationConfig with values from the file or defaults.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    simulation_data = data.get("simulation", {}) if data else {}
    return SimulationConfig(**simulation_data)
