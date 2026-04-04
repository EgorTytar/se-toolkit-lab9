"""Pydantic request/response models for the API."""

from typing import Optional

from pydantic import BaseModel, field_validator


class AIResponse(BaseModel):
    """Structured AI response returned to the client."""

    summary: str = ""
    highlights: str = ""
    insights: str = ""
    answer: str = ""

    @field_validator("summary", "highlights", "insights", "answer", mode="before")
    @classmethod
    def convert_none_to_empty_string(cls, v):
        """Some LLMs return null instead of empty string."""
        if v is None:
            return ""
        return v


class RaceSummaryResponse(BaseModel):
    """Full API response for race summary endpoints."""

    race_name: str
    circuit: str
    date: str
    season: str
    round: int
    ai_response: AIResponse


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
