"""PRISM - Social Media Simulation Framework.

This module provides the main entry point for running simulations.
"""

from pathlib import Path

from prism.simulation import (
    RoundController,
    SimulationConfig,
    SimulationResult,
    SimulationState,
    load_config,
)
from prism.simulation.executors import (
    AgentDecisionExecutor,
    AgentRoundExecutor,
    FeedRetrievalExecutor,
    LoggingExecutor,
    StateUpdateExecutor,
)


async def run_simulation(
    config_path: Path | None = None,
    config: SimulationConfig | None = None,
    state: SimulationState | None = None,
    retriever=None,
) -> SimulationResult:
    """Run a simulation with the given configuration.

    This is the main entry point for running PRISM simulations.
    You must provide either a config_path to load config from YAML,
    or a pre-built config and state.

    Args:
        config_path: Path to YAML config file (optional if config provided).
        config: Pre-built SimulationConfig (optional if config_path provided).
        state: Pre-built SimulationState with agents and posts.
        retriever: FeedRetriever instance for feed retrieval.

    Returns:
        SimulationResult with final metrics and round data.

    Raises:
        ValueError: If neither config_path nor config is provided.
        ValueError: If state is not provided.
    """
    # Load config from file if path provided
    if config_path is not None:
        config = load_config(config_path)
    elif config is None:
        raise ValueError("Either config_path or config must be provided")

    if state is None:
        raise ValueError("state must be provided with agents and posts")

    if retriever is None:
        raise ValueError("retriever must be provided for feed retrieval")

    # Build executor pipeline
    feed_exec = FeedRetrievalExecutor(retriever)
    decision_exec = AgentDecisionExecutor()
    state_exec = StateUpdateExecutor(retriever)
    logging_exec = LoggingExecutor(log_file=config.log_file)

    round_executor = AgentRoundExecutor(
        feed_executor=feed_exec,
        decision_executor=decision_exec,
        state_executor=state_exec,
        logging_executor=logging_exec,
    )

    # Run simulation
    controller = RoundController(round_executor)
    result = await controller.run_simulation(config, state)

    # Clean up
    logging_exec.close()

    return result


def main():
    """Simple greeting for backwards compatibility."""
    print("Hello from prism!")
    print("Use run_simulation() to run a simulation.")


if __name__ == "__main__":
    main()
