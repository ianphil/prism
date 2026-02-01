"""Simulation workflow loop module.

This module provides the core simulation orchestration layer that connects
PRISM's components into a working round-based simulation.

Public API:
- SimulationConfig, load_config: Configuration management
- SimulationState, EngagementMetrics: State management
- RoundController: Simulation orchestration
- Checkpointer, CheckpointData: Checkpoint persistence
- ActionResult, DecisionResult, RoundResult, SimulationResult: Result types
- create_social_media_statechart: Default statechart factory
- determine_trigger: Trigger determination logic
"""

from prism.simulation.checkpointer import CheckpointData, Checkpointer
from prism.simulation.config import SimulationConfig, load_config
from prism.simulation.controller import RoundController
from prism.simulation.protocols import SocialAgentProtocol, StatechartReasonerProtocol
from prism.simulation.results import (
    ActionResult,
    DecisionResult,
    RoundResult,
    SimulationResult,
)
from prism.simulation.state import EngagementMetrics, SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.simulation.triggers import determine_trigger

__all__ = [
    # Configuration
    "SimulationConfig",
    "load_config",
    # State
    "SimulationState",
    "EngagementMetrics",
    # Protocols
    "SocialAgentProtocol",
    "StatechartReasonerProtocol",
    # Controller
    "RoundController",
    # Checkpointing
    "Checkpointer",
    "CheckpointData",
    # Results
    "ActionResult",
    "DecisionResult",
    "RoundResult",
    "SimulationResult",
    # Factory & Triggers
    "create_social_media_statechart",
    "determine_trigger",
]
