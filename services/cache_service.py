"""AI response caching service for race summaries, retrospectives, and other AI-generated content."""

import json
import datetime
import logging
from typing import Optional, Any, Dict

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AICache

logger = logging.getLogger(__name__)

# Cache TTLs (time-to-live)
CACHE_TTL_RACE_SUMMARY = datetime.timedelta(hours=24)  # Race results don't change
CACHE_TTL_RETROSPECTIVE = datetime.timedelta(hours=12)  # Season narratives are stable
CACHE_TTL_DEFAULT = datetime.timedelta(hours=6)


async def get_cached_response(
    db: AsyncSession,
    cache_key: str,
) -> Optional[Dict[str, Any]]:
    """Get a cached AI response if it exists and hasn't expired."""
    try:
        result = await db.execute(
            select(AICache).where(AICache.cache_key == cache_key)
        )
        cached = result.scalar_one_or_none()

        if cached and cached.expires_at > datetime.datetime.utcnow():
            logger.info(f"Cache HIT for {cache_key}")
            return json.loads(cached.response_json)

        # Expired or not found
        if cached:
            logger.info(f"Cache EXPIRED for {cache_key}")
            await db.execute(delete(AICache).where(AICache.id == cached.id))
            await db.flush()

        return None
    except Exception as e:
        logger.warning(f"Cache read error for {cache_key}: {e}")
        return None


async def cache_response(
    db: AsyncSession,
    cache_key: str,
    response_data: Dict[str, Any],
    ttl: datetime.timedelta = CACHE_TTL_DEFAULT,
) -> None:
    """Cache an AI response with expiration."""
    try:
        # Delete any existing entry for this key
        await db.execute(delete(AICache).where(AICache.cache_key == cache_key))
        await db.flush()

        cached = AICache(
            cache_key=cache_key,
            response_json=json.dumps(response_data),
            created_at=datetime.datetime.utcnow(),
            expires_at=datetime.datetime.utcnow() + ttl,
        )
        db.add(cached)
        await db.flush()
        logger.info(f"Cached response for {cache_key} (TTL: {ttl})")
    except Exception as e:
        logger.warning(f"Cache write error for {cache_key}: {e}")
        # Don't fail the request if caching fails


async def invalidate_cache(db: AsyncSession, cache_key: str) -> None:
    """Manually invalidate a cached response."""
    try:
        await db.execute(delete(AICache).where(AICache.cache_key == cache_key))
        await db.flush()
    except Exception as e:
        logger.warning(f"Cache invalidation error for {cache_key}: {e}")
