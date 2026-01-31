"""Tests for SimulationConfig (T001-T006)."""

from pathlib import Path

import pytest
from pydantic import ValidationError


class TestSimulationConfigDefaults:
    """T001: Test SimulationConfig with default values."""

    def test_config_has_max_rounds_default(self):
        """SimulationConfig should have max_rounds defaulting to 10."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig()
        assert config.max_rounds == 10

    def test_config_has_checkpoint_frequency_default(self):
        """SimulationConfig should have checkpoint_frequency defaulting to 5."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig()
        assert config.checkpoint_frequency == 5

    def test_config_has_checkpoint_dir_default_none(self):
        """SimulationConfig should have checkpoint_dir defaulting to None."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig()
        assert config.checkpoint_dir is None

    def test_config_has_log_file_default_none(self):
        """SimulationConfig should have log_file defaulting to None."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig()
        assert config.log_file is None

    def test_config_allows_custom_values(self):
        """SimulationConfig should allow custom values for all fields."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(
            max_rounds=50,
            checkpoint_frequency=10,
            checkpoint_dir=Path("/tmp/checkpoints"),
            log_file=Path("/tmp/simulation.log"),
        )
        assert config.max_rounds == 50
        assert config.checkpoint_frequency == 10
        assert config.checkpoint_dir == Path("/tmp/checkpoints")
        assert config.log_file == Path("/tmp/simulation.log")


class TestSimulationConfigValidation:
    """T003: Test SimulationConfig validation (max_rounds >= 1)."""

    def test_max_rounds_zero_raises_error(self):
        """max_rounds=0 should raise ValidationError."""
        from prism.simulation.config import SimulationConfig

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(max_rounds=0)

        assert "max_rounds" in str(exc_info.value)

    def test_max_rounds_negative_raises_error(self):
        """max_rounds=-1 should raise ValidationError."""
        from prism.simulation.config import SimulationConfig

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(max_rounds=-1)

        assert "max_rounds" in str(exc_info.value)

    def test_max_rounds_one_is_valid(self):
        """max_rounds=1 should be valid (minimum)."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(max_rounds=1)
        assert config.max_rounds == 1

    def test_checkpoint_frequency_zero_raises_error(self):
        """checkpoint_frequency=0 should raise ValidationError."""
        from prism.simulation.config import SimulationConfig

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(checkpoint_frequency=0)

        assert "checkpoint_frequency" in str(exc_info.value)

    def test_checkpoint_frequency_negative_raises_error(self):
        """checkpoint_frequency=-1 should raise ValidationError."""
        from prism.simulation.config import SimulationConfig

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(checkpoint_frequency=-1)

        assert "checkpoint_frequency" in str(exc_info.value)

    def test_checkpoint_frequency_one_is_valid(self):
        """checkpoint_frequency=1 should be valid (minimum)."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(checkpoint_frequency=1)
        assert config.checkpoint_frequency == 1


class TestSimulationConfigPathParsing:
    """T005: Test Path field parsing from strings."""

    def test_checkpoint_dir_parses_from_string(self):
        """checkpoint_dir should parse Path from string."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(checkpoint_dir="/tmp/checkpoints")
        assert isinstance(config.checkpoint_dir, Path)
        assert config.checkpoint_dir == Path("/tmp/checkpoints")

    def test_log_file_parses_from_string(self):
        """log_file should parse Path from string."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(log_file="/tmp/simulation.log")
        assert isinstance(config.log_file, Path)
        assert config.log_file == Path("/tmp/simulation.log")

    def test_path_fields_accept_path_objects(self):
        """Path fields should accept Path objects directly."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(
            checkpoint_dir=Path("/var/data"),
            log_file=Path("/var/log/sim.log"),
        )
        assert config.checkpoint_dir == Path("/var/data")
        assert config.log_file == Path("/var/log/sim.log")

    def test_path_fields_accept_none(self):
        """Path fields should accept None explicitly."""
        from prism.simulation.config import SimulationConfig

        config = SimulationConfig(checkpoint_dir=None, log_file=None)
        assert config.checkpoint_dir is None
        assert config.log_file is None
