"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema returned after successful login."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user profile data."""
    id: int
    email: str
    display_name: str

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile."""
    display_name: str | None = Field(None, min_length=1, max_length=100)
