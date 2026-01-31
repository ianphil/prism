"""LLM-based Agent Reasoner for statechart transitions.

This module provides the StatechartReasoner class that uses LLM inference
to resolve ambiguous state transitions when multiple target states are valid.
"""

import json
import logging
from typing import TYPE_CHECKING, Any

from agent_framework.ollama import OllamaChatClient

from prism.statechart.states import AgentState

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent

logger = logging.getLogger(__name__)

# State descriptions used in prompt to help LLM understand options
STATE_DESCRIPTIONS: dict[AgentState, str] = {
    AgentState.IDLE: "Stop browsing, wait for next round",
    AgentState.SCROLLING: "Continue browsing without engaging",
    AgentState.EVALUATING: "Look more closely at this post",
    AgentState.COMPOSING: "Write a response or original content",
    AgentState.ENGAGING_LIKE: "Like this post",
    AgentState.ENGAGING_REPLY: "Reply to this post",
    AgentState.ENGAGING_RESHARE: "Reshare this post",
    AgentState.RESTING: "Take a break from activity",
}


def _format_context(context: Any) -> str:
    """Format context for inclusion in prompt.

    Args:
        context: Context object (e.g., Post, dict, or None)

    Returns:
        Formatted context string
    """
    if context is None:
        return ""

    if isinstance(context, dict):
        lines = ["Context:"]
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    # For other objects, try to convert to string
    return f"Context: {context}"


def build_reasoner_prompt(
    agent_name: str,
    agent_interests: list[str],
    agent_personality: str,
    current_state: AgentState,
    trigger: str,
    options: list[AgentState],
    context: Any,
) -> str:
    """Build prompt for Reasoner decision.

    Args:
        agent_name: Name of the agent
        agent_interests: List of agent's interests
        agent_personality: Agent's personality description
        current_state: Agent's current state
        trigger: Event that triggered the decision
        options: Valid target states to choose from
        context: Additional context (e.g., Post being evaluated)

    Returns:
        Formatted prompt string for LLM
    """
    options_text = "\n".join(
        f"- {opt.value}: {STATE_DESCRIPTIONS.get(opt, 'Unknown state')}"
        for opt in options
    )

    context_text = _format_context(context)

    prompt = f"""You are {agent_name}, a social media user.

Your interests: {', '.join(agent_interests)}
Your personality: {agent_personality}

You are in the "{current_state.value}" state and received "{trigger}" event.

{context_text}

Choose your next state from these options:
{options_text}

Respond with JSON only:
{{"next_state": "<state_value>"}}
"""
    return prompt


class StatechartReasoner:
    """LLM-based Agent Reasoner for ambiguous transitions.

    Implements the reasoning component of generative agent architecture,
    using the LLM to select appropriate state transitions based on
    agent profile, context, and behavioral history.
    """

    def __init__(self, client: OllamaChatClient) -> None:
        """Initialize Reasoner with LLM client.

        Args:
            client: Ollama client for inference
        """
        self._client = client

    async def decide(
        self,
        agent: "SocialAgent",
        current_state: AgentState,
        trigger: str,
        options: list[AgentState],
        context: Any = None,
    ) -> AgentState:
        """Reason about which state transition to take.

        Args:
            agent: Agent making the decision
            current_state: Agent's current state
            trigger: Event that triggered the decision
            options: Valid target states to choose from
            context: Additional context (e.g., Post being evaluated)

        Returns:
            Chosen target state from options

        Raises:
            ValueError: If options is empty

        Note:
            On parse error, returns first option as fallback
        """
        if not options:
            raise ValueError("options cannot be empty")

        # Build prompt using agent's profile
        prompt = build_reasoner_prompt(
            agent_name=agent.name,
            agent_interests=agent.interests,
            agent_personality=agent.personality,
            current_state=current_state,
            trigger=trigger,
            options=options,
            context=context,
        )

        # Call LLM
        try:
            response = await self._client.run(prompt)
            return self._parse_response(response, options)
        except Exception as e:
            logger.warning(f"Reasoner LLM call failed: {e}, using fallback")
            return options[0]

    def _parse_response(
        self,
        response_text: str,
        options: list[AgentState],
    ) -> AgentState:
        """Parse LLM response to AgentState.

        Args:
            response_text: Raw LLM response
            options: Valid options to validate against

        Returns:
            Parsed AgentState from options, or first option as fallback
        """
        try:
            data = json.loads(response_text)
            state_value = data.get("next_state", "").lower()

            for opt in options:
                if opt.value == state_value:
                    return opt

            # State not in options - fallback
            logger.warning(
                f"Reasoner returned state '{state_value}' not in options, "
                f"using fallback: {options[0].value}"
            )
            return options[0]

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse Reasoner response: {e}, using fallback")
            return options[0]
