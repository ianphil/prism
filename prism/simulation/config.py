"""Configuration models for simulation workflow.

This module defines the SimulationConfig Pydantic model that provides
configuration for simulation execution including max rounds, checkpointing,
and logging settings.
"""

from pathlib import Path

from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Configuration for simulation execution.

    Attributes:
        max_rounds: Maximum number of simulation rounds to run (must be >= 1).
        checkpoint_frequency: How often to save checkpoints (must be >= 1).
        checkpoint_dir: Directory for checkpoint files (None to disable).
        log_file: File for structured logging output (None to disable).
    """

    max_rounds: int = Field(default=10, ge=1)
    checkpoint_frequency: int = Field(default=5, ge=1)
    checkpoint_dir: Path | None = None
    log_file: Path | None = None
