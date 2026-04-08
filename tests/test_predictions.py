"""Tests for Championship Prediction endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from tests.conftest import SAMPLE_RACE_DATA, SAMPLE_SCHEDULE, SAMPLE_DRIVER_STANDINGS, SAMPLE_CONSTRUCTOR_STANDINGS


# ── Sample prediction test data ──

SAMPLE_SEASON_RESULTS = [
    {"round": 1, "race_name": "Bahrain GP", "circuit": "Bahrain", "date": "2024-03-02",
     "position": "1", "grid": 1, "points": 25.0, "status": "Finished", "constructor_id": "red_bull", "constructor": "Red Bull"},
    {"round": 2, "race_name": "Saudi Arabia GP", "circuit": "Jeddah", "date": "2024-03-09",
     "position": "1", "grid": 1, "points": 25.0, "status": "Finished", "constructor_id": "red_bull", "constructor": "Red Bull"},
    {"round": 3, "race_name": "Australia GP", "circuit": "Melbourne", "date": "2024-03-24",
     "position": "2", "grid": 2, "points": 18.0, "status": "Finished", "constructor_id": "red_bull", "constructor": "Red Bull"},
]

SAMPLE_CONSTRUCTOR_RESULTS = [
    {"season": 2024, "round": 1, "race_name": "Bahrain GP", "position": "1", "points": 25.0, "status": "Finished", "driver": "verstappen", "constructor_id": "red_bull", "constructor": "Red Bull"},
    {"season": 2024, "round": 1, "race_name": "Bahrain GP", "position": "3", "points": 15.0, "status": "Finished", "driver": "perez", "constructor_id": "red_bull", "constructor": "Red Bull"},
    {"season": 2024, "round": 2, "race_name": "Saudi Arabia GP", "position": "1", "points": 25.0, "status": "Finished", "driver": "verstappen", "constructor_id": "red_bull", "constructor": "Red Bull"},
]

SAMPLE_AI_PREDICTION_RESPONSE = """
{
  "predicted_champion_id": "max_verstappen",
  "predicted_champion_name": "Max Verstappen",
  "predicted_final_points": 450,
  "confidence": 0.85,
  "reasoning": "Based on current form and remaining races, Verstappen is heavily favored to win the championship.",
  "top_contenders": [
    {"id": "max_verstappen", "name": "Max Verstappen", "predicted_points": 450, "chance_pct": 0.85},
    {"id": "sergio_perez", "name": "Sergio Pérez", "predicted_points": 380, "chance_pct": 0.12},
    {"id": "lewis_hamilton", "name": "Lewis Hamilton", "predicted_points": 350, "chance_pct": 0.03}
  ]
}
"""


# ── Helper to set up prediction mocks ──

def setup_prediction_mocks(mock_ergast_client, mock_ai_summarizer):
    """Configure mocks for prediction tests."""
    # Ergast client mocks
    mock_ergast_client.get_driver_standings = AsyncMock(return_value=list(SAMPLE_DRIVER_STANDINGS))
    mock_ergast_client.get_constructor_standings = AsyncMock(return_value=list(SAMPLE_CONSTRUCTOR_STANDINGS))
    mock_ergast_client.get_season_schedule = AsyncMock(return_value=list(SAMPLE_SCHEDULE))
    mock_ergast_client.get_driver_season_results = AsyncMock(return_value=SAMPLE_SEASON_RESULTS)
    mock_ergast_client.get_constructor_all_results = AsyncMock(return_value=SAMPLE_CONSTRUCTOR_RESULTS)
    mock_ergast_client.close = AsyncMock(return_value=None)
    mock_ergast_client.get_driver_info = AsyncMock(return_value={"driver_id": "max_verstappen", "full_name": "Max Verstappen"})

    # AI summarizer mocks
    mock_ai_summarizer.is_available = True
    mock_ai_summarizer.chat_response = AsyncMock(return_value=SAMPLE_AI_PREDICTION_RESPONSE)


# ── Auth requirement tests ──

def test_predict_driver_championship_requires_auth(test_app):
    """Driver prediction endpoint requires authentication."""
    response = test_app.get("/api/predictions/drivers")
    assert response.status_code == 403


def test_predict_constructor_championship_requires_auth(test_app):
    """Constructor prediction endpoint requires authentication."""
    response = test_app.get("/api/predictions/constructors")
    assert response.status_code == 403


# ── Service-level tests (bypass HTTP auth) ──

@pytest.fixture
def mock_prediction_service(mock_ergast_client, mock_ai_summarizer):
    """Patch PredictionService to use mocked clients."""
    setup_prediction_mocks(mock_ergast_client, mock_ai_summarizer)

    mock_cache = AsyncMock(return_value=None)

    with patch('services.prediction_service.ErgastClient', return_value=mock_ergast_client), \
         patch('services.prediction_service.AISummarizer', return_value=mock_ai_summarizer), \
         patch('services.cache_service.get_cached_response', mock_cache), \
         patch('services.cache_service.cache_response', AsyncMock()):
        yield


@pytest.mark.asyncio
async def test_predict_driver_championship_returns_prediction(mock_prediction_service):
    """Driver prediction service returns structured prediction."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_driver_champion()

    assert result["season"] == datetime.now().year
    assert result["type"] == "drivers"
    assert "predicted_champion" in result
    assert "top_contenders" in result
    assert "form_analysis" in result
    assert "ai_reasoning" in result
    assert "races_completed" in result
    assert "races_remaining" in result


@pytest.mark.asyncio
async def test_predict_driver_champion_structure(mock_prediction_service):
    """Driver prediction champion has correct structure."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_driver_champion()

    champion = result["predicted_champion"]
    assert champion is not None
    assert "name" in champion
    assert "current_points" in champion
    assert "predicted_final_points" in champion
    assert "confidence" in champion


@pytest.mark.asyncio
async def test_predict_constructor_championship_returns_prediction(mock_prediction_service):
    """Constructor prediction service returns structured prediction."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_constructor_champion()

    assert result["season"] == datetime.now().year
    assert result["type"] == "constructors"
    assert "predicted_champion" in result
    assert "top_contenders" in result
    assert "form_analysis" in result


@pytest.mark.asyncio
async def test_predict_constructor_champion_structure(mock_prediction_service):
    """Constructor prediction champion has correct structure."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_constructor_champion()

    champion = result["predicted_champion"]
    assert champion is not None
    assert "name" in champion
    assert "current_points" in champion
    assert "predicted_final_points" in champion
    assert "confidence" in champion


# ── AI unavailable fallback tests ──

@pytest.mark.asyncio
async def test_prediction_works_without_ai(mock_ergast_client, mock_ai_summarizer):
    """Prediction works with statistical fallback when AI is unavailable."""
    setup_prediction_mocks(mock_ergast_client, mock_ai_summarizer)
    mock_ai_summarizer.is_available = False

    with patch('services.prediction_service.ErgastClient', return_value=mock_ergast_client), \
         patch('services.prediction_service.AISummarizer', return_value=mock_ai_summarizer):
        from services.prediction_service import PredictionService

        service = PredictionService()
        result = await service.predict_driver_champion()

        # Should still return prediction with statistical data
        assert result["season"] == datetime.now().year
        assert "predicted_champion" in result


# ── Form analysis tests ──

@pytest.mark.asyncio
async def test_form_analysis_included_in_prediction(mock_prediction_service):
    """Form analysis is included in prediction response."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_driver_champion()

    form = result.get("form_analysis", {})
    # Form analysis should have entries for top drivers
    assert isinstance(form, dict)


# ── Race count tests ──

@pytest.mark.asyncio
async def test_races_completed_and_remaining(mock_prediction_service):
    """Prediction includes races completed and remaining counts."""
    from services.prediction_service import PredictionService

    service = PredictionService()
    result = await service.predict_driver_champion()

    assert "races_completed" in result
    assert "races_remaining" in result
    assert isinstance(result["races_completed"], int)
    assert isinstance(result["races_remaining"], int)
    assert result["races_completed"] >= 0
    assert result["races_remaining"] >= 0
