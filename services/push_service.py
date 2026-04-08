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
    })

    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": p256dh,
            "auth": auth,
        },
    }

    logger.info(f"Sending push notification to {endpoint[:50]}...")
    logger.info(f"Notification payload: {notification}")

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
        logger.error(f"Push notification WebPushException: {e}")
        if e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        if e.response and e.response.status_code in (404, 410):
            logger.info("Push subscription expired, should be removed")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {type(e).__name__}: {e}")
        return False
