"""Social media agent implementation."""

from prism.agents.decisions import AgentDecision, Choice
from prism.agents.profiles import AgentProfile
from prism.agents.prompts import (
    build_system_prompt,
    build_user_prompt,
    parse_decision_response,
)
from prism.llm.client import OllamaChatClient
from prism.models.post import Post


class SocialAgent:
    """An LLM-powered social media agent.

    SocialAgent wraps an LLM client to make social media decisions
    based on an agent profile and feed of posts.

    Attributes:
        profile: Agent's identity and characteristics.
        client: LLM client for inference.
    """

    def __init__(
        self,
        profile: AgentProfile,
        client: OllamaChatClient,
    ) -> None:
        """Initialize a social agent.

        Args:
            profile: Agent profile with identity and interests.
            client: LLM client for making inferences.
        """
        self.profile = profile
        self.client = client
        self._system_prompt = build_system_prompt(profile)

    async def decide(self, feed: list[Post]) -> AgentDecision:
        """Decide how to engage with posts in the feed.

        Args:
            feed: List of posts to evaluate.

        Returns:
            AgentDecision with choice, reason, content, and post_id.

        Raises:
            ValueError: If the LLM response cannot be parsed.
        """
        # Build messages for the LLM
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": build_user_prompt(feed, self.profile)},
        ]

        # Get LLM response
        response = await self.client.chat(messages)

        # Determine fallback post_id (first post if available)
        fallback_post_id = feed[0].id if feed else None

        # Parse response into decision
        decision_data = parse_decision_response(response, fallback_post_id)

        # Convert to AgentDecision
        try:
            choice = Choice(decision_data["choice"])
        except ValueError:
            # Invalid choice, default to IGNORE
            choice = Choice.IGNORE
            decision_data["content"] = None

        # Validate content matches choice
        if choice in (Choice.IGNORE, Choice.LIKE):
            decision_data["content"] = None
        elif choice in (Choice.REPLY, Choice.RESHARE):
            if not decision_data.get("content"):
                # If content required but missing, use reason as fallback
                decision_data["content"] = decision_data["reason"]

        return AgentDecision(
            choice=choice,
            reason=decision_data["reason"],
            content=decision_data["content"],
            post_id=decision_data["post_id"],
        )

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.profile.name

    @property
    def interests(self) -> list[str]:
        """Get the agent's interests."""
        return self.profile.interests
