"""Pydantic request/response models for the API."""

from pydantic import BaseModel


class AIResponse(BaseModel):
    """Structured AI response returned to the client."""

    summary: str = ""
    highlights: str = ""
    insights: str = ""
    answer: str = ""


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
