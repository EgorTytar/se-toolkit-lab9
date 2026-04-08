"""Championship prediction endpoints (current season only)."""

import logging

from fastapi import APIRouter, HTTPException

from services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

logger = logging.getLogger(__name__)


@router.get("/drivers")
async def predict_driver_championship() -> dict:
    """Predict the driver championship outcome for the current season.

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (all completed races this season)
        - AI reasoning
        - Races completed/remaining
    """
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

    return result


@router.get("/constructors")
async def predict_constructor_championship() -> dict:
    """Predict the constructor championship outcome for the current season.

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (all completed races this season)
        - AI reasoning
        - Races completed/remaining
    """
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

    return result
