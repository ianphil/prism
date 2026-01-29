"""PRISM - Platform Replication for Information Spread Modeling.

A generative agent-based social media simulator for studying virality
and information spread.
"""

__version__ = "0.1.0"

# Core agent components
from prism.agents import (
    AgentDecision,
    AgentProfile,
    Choice,
    SocialAgent,
)

# Configuration
from prism.config import Config, LLMConfig, load_config

# LLM client
from prism.llm import OllamaChatClient

# Data models
from prism.models import Post

__all__ = [
    # Version
    "__version__",
    # Agents
    "AgentDecision",
    "AgentProfile",
    "Choice",
    "SocialAgent",
    # LLM
    "OllamaChatClient",
    # Config
    "Config",
    "LLMConfig",
    "load_config",
    # Models
    "Post",
]
