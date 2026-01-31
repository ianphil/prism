"""Integration tests for simulation configuration loading.

Tests that configuration can be loaded from YAML files and that
default.yaml contains the simulation section.
"""

from pathlib import Path

import pytest
import yaml

from prism.simulation.config import SimulationConfig, load_config


class TestDefaultYamlHasSimulationSection:
    """T133: Verify configs/default.yaml has simulation section."""

    @pytest.fixture
    def default_yaml_path(self) -> Path:
        """Get path to default.yaml."""
        return Path(__file__).parent.parent.parent.parent / "configs" / "default.yaml"

    def test_default_yaml_exists(self, default_yaml_path: Path) -> None:
        """Default.yaml file should exist."""
        assert default_yaml_path.exists(), f"Expected {default_yaml_path} to exist"

    def test_default_yaml_has_simulation_section(self, default_yaml_path: Path) -> None:
        """Default.yaml should have a simulation section."""
        with open(default_yaml_path) as f:
            config = yaml.safe_load(f)

        assert "simulation" in config, "Expected 'simulation' key in default.yaml"

    def test_simulation_section_has_max_rounds(self, default_yaml_path: Path) -> None:
        """Simulation section should have max_rounds."""
        with open(default_yaml_path) as f:
            config = yaml.safe_load(f)

        sim_config = config["simulation"]
        assert "max_rounds" in sim_config

    def test_simulation_section_has_checkpoint_frequency(
        self, default_yaml_path: Path
    ) -> None:
        """Simulation section should have checkpoint_frequency."""
        with open(default_yaml_path) as f:
            config = yaml.safe_load(f)

        sim_config = config["simulation"]
        assert "checkpoint_frequency" in sim_config


class TestLoadConfig:
    """T135: Verify load_config reads simulation section."""

    @pytest.fixture
    def default_yaml_path(self) -> Path:
        """Get path to default.yaml."""
        return Path(__file__).parent.parent.parent.parent / "configs" / "default.yaml"

    def test_load_config_returns_simulation_config(
        self, default_yaml_path: Path
    ) -> None:
        """load_config should return SimulationConfig."""
        config = load_config(default_yaml_path)
        assert isinstance(config, SimulationConfig)

    def test_load_config_reads_max_rounds(self, default_yaml_path: Path) -> None:
        """load_config should read max_rounds from YAML."""
        config = load_config(default_yaml_path)
        # Default is 50 per spec
        assert config.max_rounds >= 1

    def test_load_config_reads_checkpoint_frequency(
        self, default_yaml_path: Path
    ) -> None:
        """load_config should read checkpoint_frequency from YAML."""
        config = load_config(default_yaml_path)
        assert config.checkpoint_frequency >= 1

    def test_load_config_with_missing_section_uses_defaults(
        self, tmp_path: Path
    ) -> None:
        """load_config should use defaults when simulation section is missing."""
        yaml_file = tmp_path / "minimal.yaml"
        yaml_file.write_text("llm:\n  provider: ollama\n")

        config = load_config(yaml_file)
        assert isinstance(config, SimulationConfig)
        # Should use default values
        assert config.max_rounds == 10  # Default from SimulationConfig

    def test_load_config_parses_path_fields(self, tmp_path: Path) -> None:
        """load_config should convert string paths to Path objects."""
        yaml_file = tmp_path / "with_paths.yaml"
        yaml_file.write_text(
            """
simulation:
  max_rounds: 20
  checkpoint_dir: outputs/checkpoints
  log_file: outputs/decisions.jsonl
"""
        )

        config = load_config(yaml_file)
        assert config.checkpoint_dir == Path("outputs/checkpoints")
        assert config.log_file == Path("outputs/decisions.jsonl")
