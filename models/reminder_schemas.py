"""Pydantic schemas for reminder endpoints."""

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    """Schema for creating a race reminder."""
    race_round: int = Field(..., ge=1, le=30)
    race_year: int = Field(..., ge=1950, le=2100)
    notify_before_hours: int = Field(default=2, ge=1, le=168)
    method: str = Field(default="email", pattern="^(email|push)$")


class ReminderResponse(BaseModel):
    """Schema returned when listing or creating reminders."""
    id: int
    race_round: int
    race_year: int
    notify_before_hours: int
    enabled: bool
    method: str

    model_config = {"from_attributes": True}


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""
    notify_before_hours: int | None = Field(None, ge=1, le=168)
    enabled: bool | None = None
