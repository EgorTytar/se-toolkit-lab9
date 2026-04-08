"""Championship prediction endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query

from services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

logger = logging.getLogger(__name__)


@router.get("/drivers")
async def predict_driver_championship(
    year: int = Query(..., description="Season year to predict"),
) -> dict:
    """Predict the driver championship outcome for a season.

    Query param:
        year — Season year (e.g. 2025)

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (last 5 races)
        - AI reasoning
        - Races completed/remaining
    """
    service = PredictionService()

    try:
        result = await service.predict_driver_champion(year)
    except Exception as e:
        logger.error(f"Prediction error for driver championship {year}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prediction: {e}"
        ) from e

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/constructors")
async def predict_constructor_championship(
    year: int = Query(..., description="Season year to predict"),
) -> dict:
    """Predict the constructor championship outcome for a season.

    Query param:
        year — Season year (e.g. 2025)

    Returns:
        - Predicted champion with confidence level
        - Top contenders list
        - Form analysis (last 5 races)
        - AI reasoning
        - Races completed/remaining
    """
    service = PredictionService()

    try:
        result = await service.predict_constructor_champion(year)
    except Exception as e:
        logger.error(f"Prediction error for constructor championship {year}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prediction: {e}"
        ) from e

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
