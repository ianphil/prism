"""Simulation round controller.

This module provides the RoundController class that orchestrates
simulation rounds, agent processing, and checkpoint management.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from prism.simulation.checkpointer import Checkpointer
from prism.simulation.results import RoundResult, SimulationResult

if TYPE_CHECKING:
    from prism.simulation.config import SimulationConfig
    from prism.simulation.executors.round import AgentRoundExecutor
    from prism.simulation.state import SimulationState
    from prism.statechart.statechart import Statechart


class RoundController:
    """Orchestrates simulation rounds and checkpointing.

    The controller iterates through rounds, processing all agents
    each round via the round executor, and saves checkpoints at
    the configured frequency.
    """

    def __init__(self, round_executor: "AgentRoundExecutor") -> None:
        """Initialize with round executor.

        Args:
            round_executor: Executor that handles individual agent turns.
        """
        self._round_executor = round_executor
        self._checkpointer: Checkpointer | None = None

    async def run_simulation(
        self,
        config: "SimulationConfig",
        state: "SimulationState",
    ) -> SimulationResult:
        """Run complete simulation for configured rounds.

        Args:
            config: Simulation configuration.
            state: Initial simulation state.

        Returns:
            SimulationResult with final metrics and round data.
        """
        # Initialize checkpointer if directory is configured
        if config.checkpoint_dir is not None:
            self._checkpointer = Checkpointer(config.checkpoint_dir)

        rounds: list[RoundResult] = []

        # Iterate through rounds
        for _ in range(config.max_rounds):
            # Execute single round
            round_result = await self.run_round(state=state)
            rounds.append(round_result)

            # Advance to next round
            state.advance_round()

            # Save checkpoint if at frequency interval
            if self._should_checkpoint(state.round_number, config):
                self._save_checkpoint(state)

        return SimulationResult(
            total_rounds=config.max_rounds,
            final_metrics=state.metrics,
            rounds=rounds,
        )

    async def run_round(self, state: "SimulationState") -> RoundResult:
        """Execute a single simulation round.

        Processes all agents in the state via the round executor.

        Args:
            state: Current simulation state.

        Returns:
            RoundResult with decisions from all agents.
        """
        decisions = []

        for agent in state.agents:
            decision = await self._round_executor.execute(agent=agent, state=state)
            decisions.append(decision)

        return RoundResult(
            round_number=state.round_number,
            decisions=decisions,
        )

    async def resume_from_checkpoint(
        self,
        checkpoint_path: Path,
        config: "SimulationConfig",
        statechart: "Statechart",
        reasoner: Any = None,
        agent_factory: Any = None,
    ) -> SimulationResult:
        """Resume simulation from a checkpoint file.

        Loads state from checkpoint and continues simulation until
        max_rounds is reached.

        Args:
            checkpoint_path: Path to checkpoint JSON file.
            config: Simulation configuration (max_rounds is the target).
            statechart: Statechart to use (not serialized in checkpoint).
            reasoner: Optional reasoner to use.
            agent_factory: Optional callable to reconstruct agents.

        Returns:
            SimulationResult with final metrics.
        """
        # Load checkpoint
        checkpointer = Checkpointer(checkpoint_path.parent)
        state = checkpointer.load(
            path=checkpoint_path,
            statechart=statechart,
            reasoner=reasoner,
            agent_factory=agent_factory,
        )

        # Initialize checkpointer for saving if configured
        if config.checkpoint_dir is not None:
            self._checkpointer = Checkpointer(config.checkpoint_dir)

        # Calculate remaining rounds
        start_round = state.round_number
        remaining_rounds = config.max_rounds - start_round

        rounds: list[RoundResult] = []

        # Continue simulation
        for _ in range(remaining_rounds):
            round_result = await self.run_round(state=state)
            rounds.append(round_result)

            state.advance_round()

            if self._should_checkpoint(state.round_number, config):
                self._save_checkpoint(state)

        return SimulationResult(
            total_rounds=config.max_rounds,
            final_metrics=state.metrics,
            rounds=rounds,
        )

    def _should_checkpoint(
        self,
        round_number: int,
        config: "SimulationConfig",
    ) -> bool:
        """Determine if checkpoint should be saved at this round.

        Args:
            round_number: Current round number (after advance).
            config: Simulation configuration.

        Returns:
            True if checkpoint should be saved.
        """
        if config.checkpoint_dir is None:
            return False
        return round_number % config.checkpoint_frequency == 0

    def _save_checkpoint(self, state: "SimulationState") -> Path | None:
        """Save checkpoint if checkpointer is configured.

        Args:
            state: Current simulation state.

        Returns:
            Path to saved checkpoint, or None if not saved.
        """
        if self._checkpointer is None:
            return None
        return self._checkpointer.save(state)
