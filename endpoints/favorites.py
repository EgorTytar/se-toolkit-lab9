"""User favorites endpoints: manage favorite drivers and constructors."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User, UserFavorite
from dependencies import get_current_user
from services.ergast_client import ErgastClient

router = APIRouter(prefix="/api/users/me/favorites", tags=["favorites"])

_ergast = ErgastClient()


class FavoriteRequest(BaseModel):
    driver_id: str | None = None
    constructor_id: str | None = None


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

    items = []
    for f in favorites:
        if f.driver_id:
            try:
                info = await _ergast.get_driver_info(f.driver_id)
                items.append({
                    "id": f.id,
                    "driver_id": f.driver_id,
                    "driver_code": info.get("code", ""),
                    "driver_name": info.get("full_name", f.driver_id),
                    "constructor_id": None,
                    "constructor_name": None,
                    "created_at": f.created_at.isoformat() if f.created_at else "",
                })
            except Exception:
                items.append({
                    "id": f.id,
                    "driver_id": f.driver_id,
                    "driver_code": "",
                    "driver_name": f.driver_id,
                    "constructor_id": None,
                    "constructor_name": None,
                    "created_at": f.created_at.isoformat() if f.created_at else "",
                })
        elif f.constructor_id:
            try:
                info = await _ergast.get_constructor_info(f.constructor_id)
                items.append({
                    "id": f.id,
                    "driver_id": None,
                    "driver_code": None,
                    "driver_name": None,
                    "constructor_id": f.constructor_id,
                    "constructor_name": info.get("name", f.constructor_id),
                    "created_at": f.created_at.isoformat() if f.created_at else "",
                })
            except Exception:
                items.append({
                    "id": f.id,
                    "driver_id": None,
                    "driver_code": None,
                    "driver_name": None,
                    "constructor_id": f.constructor_id,
                    "constructor_name": f.constructor_id,
                    "created_at": f.created_at.isoformat() if f.created_at else "",
                })

    await _ergast.close()
    return items


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    body: FavoriteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a favorite driver or constructor."""
    if not body.driver_id and not body.constructor_id:
        raise HTTPException(
            status_code=400, detail="Provide driver_id or constructor_id"
        )

    fav = UserFavorite(
        user_id=user.id, driver_id=body.driver_id, constructor_id=body.constructor_id
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
