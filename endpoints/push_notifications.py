"""Push notification subscription endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import PushSubscription, User
from dependencies import get_current_user
from config import VAPID_PUBLIC_KEY

router = APIRouter(prefix="/api/push", tags=["push-notifications"])
logger = logging.getLogger(__name__)


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Return the VAPID public key for browser subscription."""
    if VAPID_PUBLIC_KEY == "your-vapid-public-key-here":
        raise HTTPException(status_code=503, detail="VAPID keys not configured")
    return {"public_key": VAPID_PUBLIC_KEY}


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}


@router.post("/subscribe")
async def subscribe_to_push(
    request: PushSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a browser push notification subscription for the current user."""
    subscription = PushSubscription(
        user_id=user.id,
        endpoint=request.endpoint,
        p256dh=request.keys.get("p256dh", ""),
        auth=request.keys.get("auth", ""),
    )

    # Check if this endpoint already exists (update instead of duplicate)
    from sqlalchemy import select
    existing = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == request.endpoint,
        )
    )
    existing = existing.scalar_one_or_none()

    if existing:
        existing.p256dh = request.keys.get("p256dh", "")
        existing.auth = request.keys.get("auth", "")
    else:
        db.add(subscription)

    await db.commit()
    return {"status": "subscribed"}


@router.post("/unsubscribe")
async def unsubscribe_from_push(
    request: PushSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a browser push notification subscription."""
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == request.endpoint,
        )
    )
    await db.commit()
    return {"status": "unsubscribed"}


@router.get("/subscriptions")
async def get_push_subscriptions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all push notification subscriptions for the current user."""
    from sqlalchemy import select
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id).order_by(PushSubscription.created_at)
    )
    subscriptions = result.scalars().all()
    return {
        "subscriptions": [
            {
                "id": s.id,
                "endpoint": s.endpoint,
                "created_at": s.created_at.isoformat(),
            }
            for s in subscriptions
        ]
    }
