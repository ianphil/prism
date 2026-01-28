"""Structured output model for social agent decisions."""

from typing import Literal

from pydantic import BaseModel, field_validator


class AgentDecision(BaseModel):
    """Structured output of a social agent's decision."""

    choice: Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
    reason: str
    content: str | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must be non-empty")
        return v

    @field_validator("content")
    @classmethod
    def content_required_for_reply_reshare(cls, v: str | None, info) -> str | None:
        choice = info.data.get("choice")
        if choice in ("REPLY", "RESHARE") and (v is None or not v.strip()):
            raise ValueError(f"content is required when choice is {choice}")
        return v
