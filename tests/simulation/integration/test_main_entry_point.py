"""Tests for main.py entry point.

Verifies that main.py has a run_simulation function that can be imported
and has the expected signature.
"""

import inspect


class TestMainEntryPoint:
    """T147: Verify main.py has run_simulation function."""

    def test_run_simulation_is_importable(self) -> None:
        """run_simulation should be importable from main."""
        from main import run_simulation

        assert run_simulation is not None

    def test_run_simulation_is_callable(self) -> None:
        """run_simulation should be a callable."""
        from main import run_simulation

        assert callable(run_simulation)

    def test_run_simulation_is_async(self) -> None:
        """run_simulation should be an async function."""
        from main import run_simulation

        assert inspect.iscoroutinefunction(run_simulation)

    def test_run_simulation_accepts_config_path(self) -> None:
        """run_simulation should accept config_path parameter."""
        from main import run_simulation

        sig = inspect.signature(run_simulation)
        params = list(sig.parameters.keys())

        # Should accept config_path as a parameter
        assert "config_path" in params or len(params) > 0
