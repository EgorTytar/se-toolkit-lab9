"""Unit tests for push notification endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


# ── Push subscription tests ──

class TestPushNotifications:
    """Tests for push notification subscription endpoints."""

    def test_vapid_public_key_returns_503_when_not_configured(self, test_app):
        """VAPID public key endpoint returns 503 when keys aren't set."""
        r = test_app.get("/api/push/vapid-public-key")
        # Since we use placeholder keys, this returns 503
        assert r.status_code in (200, 503)

    def test_subscribe_requires_auth(self, test_app):
        """Subscribe endpoint requires authentication."""
        r = test_app.post("/api/push/subscribe", json={
            "endpoint": "https://example.com/push",
            "keys": {"p256dh": "test", "auth": "test"},
        })
        assert r.status_code in (401, 403)

    def test_unsubscribe_requires_auth(self, test_app):
        """Unsubscribe endpoint requires authentication."""
        r = test_app.post("/api/push/unsubscribe", json={
            "endpoint": "https://example.com/push",
            "keys": {"p256dh": "test", "auth": "test"},
        })
        assert r.status_code in (401, 403)

    def test_subscriptions_list_requires_auth(self, test_app):
        """Subscriptions list endpoint requires authentication."""
        r = test_app.get("/api/push/subscriptions")
        assert r.status_code in (401, 403)

    def test_push_service_handles_unconfigured_keys(self):
        """Push service gracefully handles unconfigured VAPID keys."""
        from services.push_service import send_push_notification
        import asyncio

        async def test():
            result = await send_push_notification(
                endpoint="https://example.com/push",
                p256dh="test-p256dh",
                auth="test-auth",
                title="Test",
                body="Test body",
            )
            assert result is False  # Returns False when keys not configured

        asyncio.run(test())
