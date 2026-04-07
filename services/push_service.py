"""Push notification service using Web Push API (pywebpush)."""

import json
import logging

from pywebpush import webpush, WebPushException

from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS

logger = logging.getLogger(__name__)


async def send_push_notification(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
) -> bool:
    """Send a web push notification to a browser subscription.

    Returns True on success, False on failure (logs errors instead of raising).
    """
    # Check if VAPID keys are configured
    if VAPID_PRIVATE_KEY == "your-vapid-private-key-here":
        logger.warning("Push notification skipped: VAPID keys not configured")
        return False

    notification = json.dumps({
        "title": title,
        "body": body,
        "icon": "/icon-192.png",
        "badge": "/badge-72.png",
    })

    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": p256dh,
            "auth": auth,
        },
    }

    try:
        response = webpush(
            subscription_info=subscription_info,
            data=notification,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )
        logger.info(f"Push notification sent: {response.status_code}")
        return True
    except WebPushException as e:
        if e.response and e.response.status_code in (404, 410):
            # Subscription expired — caller should remove it from DB
            logger.info(f"Push subscription expired, should be removed: {e}")
        else:
            logger.error(f"Push notification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {e}")
        return False
