"""Agent decision types and structures."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Choice(str, Enum):
    """Possible agent actions for a post."""

    IGNORE = "IGNORE"
    LIKE = "LIKE"
    REPLY = "REPLY"
    RESHARE = "RESHARE"


@dataclass
class AgentDecision:
    """Structured output from an agent's decision-making process.

    Attributes:
        choice: The action the agent decided to take.
        reason: 1-2 sentence explanation of why.
        post_id: ID of the post being acted upon.
        content: Generated text for REPLY/RESHARE (None for IGNORE/LIKE).
        timestamp: When the decision was made.
    """

    choice: Choice
    reason: str
    post_id: str
    content: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate that content matches choice type."""
        if not self.reason:
            raise ValueError("reason must be a non-empty string")

        if self.choice in (Choice.IGNORE, Choice.LIKE):
            if self.content is not None:
                raise ValueError(
                    f"content must be None for {self.choice.value}, got: {self.content}"
                )
        elif self.choice in (Choice.REPLY, Choice.RESHARE):
            if self.content is None:
                raise ValueError(f"content is required for {self.choice.value}")
