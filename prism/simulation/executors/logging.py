"""Logging executor for simulation pipeline.

This module provides the LoggingExecutor that records agent decisions
to structured JSON logs for debugging and analysis.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from prism.simulation.results import DecisionResult
    from prism.simulation.state import SimulationState


class LoggingExecutor:
    """Logs agent decisions to structured JSON.

    Writes to Python logger and optionally to a JSON lines file for
    post-hoc analysis of simulation decisions.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        log_file: Path | None = None,
    ) -> None:
        """Initialize with optional logger and file path.

        Args:
            logger: Python logger to use. Defaults to prism.simulation.decisions.
            log_file: Optional path to write JSON lines. Creates parent dirs.
        """
        self._logger = logger or logging.getLogger("prism.simulation.decisions")
        self._log_file = log_file
        self._file_handle: TextIO | None = None

        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(log_file, "a")

    async def execute(
        self,
        agent: Any,
        state: "SimulationState",
        decision: "DecisionResult",
    ) -> None:
        """Log the decision to structured output.

        Args:
            agent: The agent (unused, for protocol compliance).
            state: Current simulation state.
            decision: The decision result to log.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round": state.round_number,
            "agent_id": decision.agent_id,
            "trigger": decision.trigger,
            "from_state": decision.from_state.value,
            "to_state": decision.to_state.value,
            "action_type": decision.action.action if decision.action else None,
            "reasoner_used": decision.reasoner_used,
        }

        json_entry = json.dumps(entry)
        self._logger.info(json_entry)

        if self._file_handle is not None:
            self._file_handle.write(json_entry + "\n")
            self._file_handle.flush()

    def close(self) -> None:
        """Close file handle if open."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def __del__(self) -> None:
        """Ensure file handle is closed on deletion."""
        self.close()
