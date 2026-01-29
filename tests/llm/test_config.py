"""Tests for LLMConfig, PrismConfig, and load_config."""

import pytest
from pydantic import ValidationError

from prism.llm.config import LLMConfig, PrismConfig, load_config


class TestLLMConfigDefaults:
    def test_default_provider(self):
        config = LLMConfig()
        assert config.provider == "ollama"

    def test_default_host(self):
        config = LLMConfig()
        assert config.host == "http://localhost:11434"

    def test_default_model_id(self):
        config = LLMConfig()
        assert config.model_id == "mistral"

    def test_default_temperature(self):
        config = LLMConfig()
        assert config.temperature == 0.7

    def test_default_max_tokens(self):
        config = LLMConfig()
        assert config.max_tokens == 512

    def test_default_seed_is_none(self):
        config = LLMConfig()
        assert config.seed is None


class TestLLMConfigValid:
    def test_custom_values(self):
        config = LLMConfig(
            provider="ollama",
            host="http://myhost:11434",
            model_id="qwen2.5",
            temperature=1.0,
            max_tokens=1024,
            seed=42,
        )
        assert config.host == "http://myhost:11434"
        assert config.model_id == "qwen2.5"
        assert config.temperature == 1.0
        assert config.max_tokens == 1024
        assert config.seed == 42

    def test_temperature_at_zero(self):
        config = LLMConfig(temperature=0.0)
        assert config.temperature == 0.0

    def test_temperature_at_max(self):
        config = LLMConfig(temperature=2.0)
        assert config.temperature == 2.0


class TestLLMConfigInvalid:
    def test_temperature_below_zero_raises_error(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

    def test_temperature_above_two_raises_error(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_zero_raises_error(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_max_tokens_negative_raises_error(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=-1)


class TestPrismConfig:
    def test_default_has_llm(self):
        config = PrismConfig()
        assert isinstance(config.llm, LLMConfig)

    def test_custom_llm(self):
        config = PrismConfig(llm=LLMConfig(model_id="phi3"))
        assert config.llm.model_id == "phi3"


class TestLoadConfig:
    def test_loads_valid_yaml(self, tmp_path):
        yaml_content = (
            "llm:\n"
            "  provider: ollama\n"
            "  host: http://localhost:11434\n"
            "  model_id: qwen2.5\n"
            "  temperature: 0.5\n"
            "  max_tokens: 256\n"
        )
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml_content)

        config = load_config(config_file)
        assert isinstance(config, PrismConfig)
        assert config.llm.model_id == "qwen2.5"
        assert config.llm.temperature == 0.5
        assert config.llm.max_tokens == 256

    def test_returns_prism_config_with_llm(self, tmp_path):
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("llm:\n  model_id: phi3\n")

        config = load_config(config_file)
        assert isinstance(config, PrismConfig)
        assert isinstance(config.llm, LLMConfig)
        assert config.llm.model_id == "phi3"

    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_invalid_values_raise_validation_error(self, tmp_path):
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("llm:\n  temperature: 5.0\n")

        with pytest.raises(ValidationError):
            load_config(config_file)

    def test_empty_yaml_returns_defaults(self, tmp_path):
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = load_config(config_file)
        assert config.llm.model_id == "mistral"
        assert config.llm.temperature == 0.7
