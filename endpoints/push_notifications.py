"""Push notification subscription endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import PushSubscription, User
from dependencies import get_current_user
from config import VAPID_PUBLIC_KEY
from services.push_service import send_push_notification

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


@router.post("/test")
async def send_test_push_notification(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a test push notification to all of the user's subscriptions."""
    subs_result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id)
    )
    subs = subs_result.scalars().all()

    if not subs:
        raise HTTPException(status_code=400, detail="No push subscriptions found")

    logger.info(f"User {user.id} has {len(subs)} push subscriptions")

    expired_subs = []
    sent_count = 0
    for sub in subs:
        logger.info(f"Sending push to endpoint: {sub.endpoint[:50]}...")
        success = await send_push_notification(
            endpoint=sub.endpoint,
            p256dh=sub.p256dh,
            auth=sub.auth,
            title="🏎️ F1 Assistant",
            body="Test notification — push notifications are working!",
        )
        if success:
            sent_count += 1
            logger.info(f"Push sent successfully to {sub.endpoint[:50]}...")
        else:
            expired_subs.append(sub)
            logger.warning(f"Push failed for {sub.endpoint[:50]}...")

    # Clean up expired subscriptions
    for expired in expired_subs:
        await db.delete(expired)
    if expired_subs:
        await db.commit()

    if sent_count == 0:
        raise HTTPException(status_code=500, detail="Failed to send test notification")

    return {"status": "sent", "count": sent_count}


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
