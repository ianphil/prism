"""Tests for configuration loading."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from prism.config.settings import (
    Config,
    LLMConfig,
    get_default_config,
    load_config,
)


class TestLLMConfig:
    """Tests for LLMConfig validation."""

    def test_default_values(self) -> None:
        """LLMConfig should have sensible defaults."""
        config = LLMConfig()
        assert config.endpoint == "http://localhost:11434"
        assert config.model == "mistral"
        assert config.reasoning_effort == "medium"
        assert config.timeout == 30
        assert config.temperature == 0.7

    def test_custom_values(self) -> None:
        """LLMConfig should accept custom values."""
        config = LLMConfig(
            endpoint="http://custom:8080",
            model="llama3",
            reasoning_effort="high",
            timeout=60,
            temperature=0.5,
        )
        assert config.endpoint == "http://custom:8080"
        assert config.model == "llama3"
        assert config.reasoning_effort == "high"
        assert config.timeout == 60
        assert config.temperature == 0.5

    def test_endpoint_trailing_slash_stripped(self) -> None:
        """Trailing slash on endpoint should be stripped."""
        config = LLMConfig(endpoint="http://localhost:11434/")
        assert config.endpoint == "http://localhost:11434"

    def test_invalid_endpoint_raises(self) -> None:
        """Invalid endpoint should raise ValidationError."""
        with pytest.raises(ValidationError, match="endpoint must start with"):
            LLMConfig(endpoint="localhost:11434")

    def test_invalid_reasoning_effort_raises(self) -> None:
        """Invalid reasoning_effort should raise ValidationError."""
        with pytest.raises(ValidationError):
            LLMConfig(reasoning_effort="ultra")  # type: ignore

    def test_invalid_timeout_raises(self) -> None:
        """Timeout <= 0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            LLMConfig(timeout=0)

    def test_invalid_temperature_raises(self) -> None:
        """Temperature outside 0-2 range should raise ValidationError."""
        with pytest.raises(ValidationError):
            LLMConfig(temperature=3.0)


class TestConfig:
    """Tests for the root Config object."""

    def test_default_config(self) -> None:
        """Config should have defaults for all sections."""
        config = Config()
        assert config.llm is not None
        assert config.agent is not None
        assert config.logging is not None

    def test_config_with_partial_data(self) -> None:
        """Config should fill in missing sections with defaults."""
        config = Config(llm=LLMConfig(model="llama3"))
        assert config.llm.model == "llama3"
        expected = "curious and engaged social media user"
        assert config.agent.default_personality == expected


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_defaults(self) -> None:
        """load_config() without path should return defaults."""
        config = load_config()
        assert config.llm.model == "mistral"

    def test_load_config_from_file(self, tmp_path: Path) -> None:
        """load_config() should load from YAML file."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  model: "llama3"
  timeout: 60
""")
        config = load_config(config_file)
        assert config.llm.model == "llama3"
        assert config.llm.timeout == 60
        # Defaults should still apply for unspecified values
        assert config.llm.endpoint == "http://localhost:11434"

    def test_load_config_file_not_found(self) -> None:
        """load_config() should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_config("/nonexistent/config.yaml")

    def test_load_config_empty_file(self, tmp_path: Path) -> None:
        """load_config() should handle empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        config = load_config(config_file)
        assert config.llm.model == "mistral"  # Default

    def test_load_config_env_override_endpoint(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Environment variables should override file values."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  endpoint: "http://file:11434"
""")
        monkeypatch.setenv("PRISM_LLM_ENDPOINT", "http://env:11434")

        config = load_config(config_file)
        assert config.llm.endpoint == "http://env:11434"

    def test_load_config_env_override_model(self, monkeypatch) -> None:
        """PRISM_LLM_MODEL should override model."""
        monkeypatch.setenv("PRISM_LLM_MODEL", "llama3:70b")

        config = load_config()
        assert config.llm.model == "llama3:70b"

    def test_load_config_env_override_timeout(self, monkeypatch) -> None:
        """PRISM_LLM_TIMEOUT should override timeout."""
        monkeypatch.setenv("PRISM_LLM_TIMEOUT", "120")

        config = load_config()
        assert config.llm.timeout == 120

    def test_load_config_env_override_log_level(self, monkeypatch) -> None:
        """PRISM_LOG_LEVEL should override logging level."""
        monkeypatch.setenv("PRISM_LOG_LEVEL", "debug")

        config = load_config()
        assert config.logging.level == "DEBUG"


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_config(self) -> None:
        """get_default_config should return a Config object."""
        config = get_default_config()
        assert isinstance(config, Config)
        assert config.llm.model == "mistral"
