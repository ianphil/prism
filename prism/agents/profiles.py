"""Agent profile definitions."""

from dataclasses import dataclass, field


@dataclass
class AgentProfile:
    """Identity and characteristics of a social media agent.

    Attributes:
        id: Unique agent identifier.
        name: Display name.
        interests: Topics the agent cares about.
        personality: Personality description.
        stance: Positions on topics (topic -> position mapping).
    """

    id: str
    name: str
    interests: list[str] = field(default_factory=list)
    personality: str = "neutral"
    stance: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate profile fields."""
        if not self.id:
            raise ValueError("id must be a non-empty string")
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if not self.interests:
            raise ValueError("interests must have at least one item")
