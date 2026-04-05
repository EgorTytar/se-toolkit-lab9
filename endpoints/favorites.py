"""User favorites endpoints: manage favorite drivers and constructors."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User, UserFavorite
from dependencies import get_current_user

router = APIRouter(prefix="/api/users/me/favorites", tags=["favorites"])


@router.get("/", response_model=list[dict])
async def list_favorites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all favorite drivers/teams for the current user."""
    result = await db.execute(
        select(UserFavorite).where(UserFavorite.user_id == user.id)
    )
    favorites = result.scalars().all()
    return [
        {"id": f.id, "driver_id": f.driver_id, "constructor_id": f.constructor_id}
        for f in favorites
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    driver_id: str | None = None,
    constructor_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a favorite driver or constructor."""
    if not driver_id and not constructor_id:
        raise HTTPException(
            status_code=400, detail="Provide driver_id or constructor_id"
        )

    fav = UserFavorite(
        user_id=user.id, driver_id=driver_id, constructor_id=constructor_id
    )
    db.add(fav)
    await db.flush()
    return {
        "id": fav.id,
        "driver_id": fav.driver_id,
        "constructor_id": fav.constructor_id,
    }


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    favorite_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a favorite driver or constructor."""
    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.id == favorite_id, UserFavorite.user_id == user.id
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.delete(fav)
    await db.flush()
