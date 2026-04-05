"""User profile endpoints: get and update current user profile."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from dependencies import get_current_user
from models.auth_schemas import UpdateProfileRequest, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current authenticated user's profile."""
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the current authenticated user's profile."""
    if body.display_name is not None:
        user.display_name = body.display_name
        db.add(user)
        await db.flush()

    return user
