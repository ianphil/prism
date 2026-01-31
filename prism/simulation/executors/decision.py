"""Agent decision executor for simulation pipeline.

This module provides the AgentDecisionExecutor that handles the statechart-driven
decision flow for agents, including trigger determination, statechart firing,
reasoner invocation for ambiguous cases, and action execution.
"""

import logging
from typing import TYPE_CHECKING, Any

from prism.rag.models import Post
from prism.simulation.results import ActionResult, DecisionResult
from prism.simulation.triggers import determine_trigger
from prism.statechart.states import AgentState

if TYPE_CHECKING:
    from prism.simulation.state import SimulationState

logger = logging.getLogger(__name__)


class AgentDecisionExecutor:
    """Executes statechart-driven agent decisions.

    Handles the full decision flow:
    1. Tick agent time-in-state
    2. Determine trigger from context (or timeout)
    3. Fire statechart transition
    4. Invoke reasoner if ambiguous (multiple valid targets)
    5. Transition agent to new state
    6. Execute action based on new state
    """

    async def execute(
        self,
        agent: Any,
        state: "SimulationState",
        feed: list[Post],
    ) -> DecisionResult:
        """Execute decision logic for one agent turn.

        Args:
            agent: The agent making the decision.
            state: Current simulation state with statechart and reasoner.
            feed: Feed posts retrieved for this agent.

        Returns:
            DecisionResult with state transition and action details.
        """
        # 1. Tick time-in-state
        agent.tick()

        # Store the from_state before any transition
        from_state = agent.state

        # 2. Determine trigger
        if agent.is_timed_out():
            trigger = "timeout"
        else:
            trigger = determine_trigger(agent, feed, state)

        # 3. Fire statechart transition
        new_state = state.statechart.fire(
            trigger=trigger,
            current_state=agent.state,
            agent=agent,
            context={"feed": feed, "state": state},
        )

        reasoner_used = False

        # 4. Handle ambiguous transitions (fire returned None but valid targets exist)
        if new_state is None:
            targets = state.statechart.valid_targets(agent.state, trigger)
            if len(targets) > 1 and state.reasoner is not None:
                # Multiple targets and reasoner available - use LLM to decide
                new_state = await state.reasoner.decide(
                    agent=agent,
                    current_state=agent.state,
                    trigger=trigger,
                    options=targets,
                    context={"feed": feed},
                )
                reasoner_used = True
            elif len(targets) == 1:
                # Single target - use it
                new_state = targets[0]
            elif len(targets) > 1:
                # Multiple targets but no reasoner - use first one as fallback
                logger.warning(
                    "Agent %s: multiple targets %s but no reasoner. Using fallback: %s",
                    agent.agent_id,
                    [t.value for t in targets],
                    targets[0].value,
                )
                new_state = targets[0]
            # else: no valid targets - stay in current state

        # 5. Transition agent to new state (if changed)
        if new_state is not None and new_state != agent.state:
            ctx = {"round": state.round_number}
            agent.transition_to(new_state, trigger, context=ctx)
        else:
            # Stay in current state if no valid transition
            new_state = agent.state

        # 6. Execute action based on the state we were in (before transition)
        action = self._execute_action(from_state, feed)

        return DecisionResult(
            agent_id=agent.agent_id,
            trigger=trigger,
            from_state=from_state,
            to_state=new_state,
            action=action,
            reasoner_used=reasoner_used,
        )

    def _execute_action(
        self,
        from_state: AgentState,
        feed: list[Post],
    ) -> ActionResult:
        """Execute action based on agent's state before transition.

        Actions are based on what state the agent was in, not where they're going.
        E.g., COMPOSING state means they were composing, action is "compose".
             ENGAGING_LIKE means they were liking, action is "like".

        Args:
            from_state: Agent's state before transition.
            feed: Feed posts for target selection.

        Returns:
            ActionResult describing the action taken.
        """
        target_post = feed[0] if feed else None
        target_post_id = target_post.id if target_post else None

        match from_state:
            case AgentState.COMPOSING:
                return ActionResult(
                    action="compose",
                    target_post_id=None,
                    content=None,  # Content would be generated by LLM
                )
            case AgentState.ENGAGING_LIKE:
                return ActionResult(
                    action="like",
                    target_post_id=target_post_id,
                )
            case AgentState.ENGAGING_REPLY:
                return ActionResult(
                    action="reply",
                    target_post_id=target_post_id,
                    content=None,  # Content would be generated by LLM
                )
            case AgentState.ENGAGING_RESHARE:
                return ActionResult(
                    action="reshare",
                    target_post_id=target_post_id,
                )
            case _:
                # IDLE, SCROLLING, EVALUATING, RESTING - no engagement action
                return ActionResult(
                    action="scroll",
                    target_post_id=None,
                )
