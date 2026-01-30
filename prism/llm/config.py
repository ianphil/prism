"""LLM configuration models and YAML loading."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from prism.rag.config import RAGConfig


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
    rag: RAGConfig = RAGConfig()


def load_config(path: str | Path = "configs/default.yaml") -> PrismConfig:
    """Load and validate PRISM configuration from YAML.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Validated PrismConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
        pydantic.ValidationError: If the config values are invalid.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return PrismConfig()

    return PrismConfig(**raw)
