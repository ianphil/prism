"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Configuration for the LLM client.

    Attributes:
        endpoint: Ollama API endpoint URL.
        model: Model name to use.
        reasoning_effort: Reasoning effort level (low/medium/high).
        timeout: Request timeout in seconds.
        temperature: Sampling temperature (0.0-2.0).
    """

    endpoint: str = Field(default="http://localhost:11434")
    model: str = Field(default="mistral")
    reasoning_effort: Literal["low", "medium", "high"] = Field(default="medium")
    timeout: int = Field(default=30, gt=0)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Ensure endpoint is a valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("endpoint must start with http:// or https://")
        return v.rstrip("/")


class AgentConfig(BaseModel):
    """Configuration for agent behavior.

    Attributes:
        default_personality: Default personality for new agents.
    """

    default_personality: str = Field(default="curious and engaged social media user")


class LoggingConfig(BaseModel):
    """Configuration for logging.

    Attributes:
        level: Logging level.
    """

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")


class Config(BaseModel):
    """Root configuration object.

    Attributes:
        llm: LLM client configuration.
        agent: Agent behavior configuration.
        logging: Logging configuration.
    """

    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a YAML file.

    Configuration values can be overridden by environment variables:
    - PRISM_LLM_ENDPOINT: Override llm.endpoint
    - PRISM_LLM_MODEL: Override llm.model
    - PRISM_LLM_TIMEOUT: Override llm.timeout
    - PRISM_LOG_LEVEL: Override logging.level

    Args:
        path: Path to YAML configuration file. If None, uses defaults.

    Returns:
        Validated configuration object.

    Raises:
        FileNotFoundError: If path is provided but file doesn't exist.
        ValidationError: If configuration values are invalid.
    """
    data: dict = {}

    # Load from file if provided
    if path is not None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

    # Apply environment variable overrides
    data = _apply_env_overrides(data)

    return Config(**data)


def _apply_env_overrides(data: dict) -> dict:
    """Apply environment variable overrides to config data.

    Args:
        data: Configuration dictionary.

    Returns:
        Configuration dictionary with environment overrides applied.
    """
    # Ensure nested dicts exist
    if "llm" not in data:
        data["llm"] = {}
    if "logging" not in data:
        data["logging"] = {}

    # LLM overrides
    if endpoint := os.environ.get("PRISM_LLM_ENDPOINT"):
        data["llm"]["endpoint"] = endpoint
    if model := os.environ.get("PRISM_LLM_MODEL"):
        data["llm"]["model"] = model
    if timeout := os.environ.get("PRISM_LLM_TIMEOUT"):
        data["llm"]["timeout"] = int(timeout)

    # Logging overrides
    if level := os.environ.get("PRISM_LOG_LEVEL"):
        data["logging"]["level"] = level.upper()

    return data


def get_default_config() -> Config:
    """Get the default configuration.

    Returns:
        Default configuration object.
    """
    return Config()
