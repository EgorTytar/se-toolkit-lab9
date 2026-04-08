"""Championship prediction endpoints (current season only)."""

import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from dependencies import get_current_user
from services.cache_service import get_cached_response, cache_response
from services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

logger = logging.getLogger(__name__)

# Predictions cached for 6 hours (data changes between races only)
CACHE_TTL_PREDICTION = datetime.timedelta(hours=6)


@router.get("/drivers")
async def predict_driver_championship(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Predict the driver championship outcome for the current season.

    Requires authentication. Results are cached for 6 hours.

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (all completed races this season)
        - AI reasoning
        - Races completed/remaining
    """
    cache_key = "prediction_drivers"
    cached = await get_cached_response(db, cache_key)
    if cached:
        logger.info("Returning cached driver prediction")
        return cached

    service = PredictionService()

    try:
        result = await service.predict_driver_champion()
    except Exception as e:
        logger.error(f"Prediction error for driver championship: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prediction: {e}"
        ) from e

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Cache the prediction
    try:
        await cache_response(db, cache_key, result, CACHE_TTL_PREDICTION)
    except Exception as cache_err:
        logger.warning(f"Cache write failed for driver prediction: {cache_err}")

    return result


@router.get("/constructors")
async def predict_constructor_championship(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Predict the constructor championship outcome for the current season.

    Requires authentication. Results are cached for 6 hours.

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (all completed races this season)
        - AI reasoning
        - Races completed/remaining
    """
    cache_key = "prediction_constructors"
    cached = await get_cached_response(db, cache_key)
    if cached:
        logger.info("Returning cached constructor prediction")
        return cached

    service = PredictionService()

    try:
        result = await service.predict_constructor_champion()
    except Exception as e:
        logger.error(f"Prediction error for constructor championship: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prediction: {e}"
        ) from e

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Cache the prediction
    try:
        await cache_response(db, cache_key, result, CACHE_TTL_PREDICTION)
    except Exception as cache_err:
        logger.warning(f"Cache write failed for constructor prediction: {cache_err}")

    return result
