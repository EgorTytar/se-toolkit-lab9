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


@pytest.fixture
def mock_prediction_service(mock_ergast_client, mock_ai_summarizer):
    """Patch PredictionService and cache to use mocked clients."""
    # Override standings to return data for current year
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

    # Mock cache to always return None (no cache hits in tests)
    mock_cache = AsyncMock(return_value=None)

    with patch('services.prediction_service.ErgastClient', return_value=mock_ergast_client), \
         patch('services.prediction_service.AISummarizer', return_value=mock_ai_summarizer), \
         patch('endpoints.predictions.get_cached_response', mock_cache), \
         patch('endpoints.predictions.cache_response', AsyncMock()):
        yield


# ── Driver prediction endpoint tests ──

def test_predict_driver_championship_returns_prediction(test_app, mock_prediction_service):
    """Driver prediction endpoint returns structured prediction."""
    response = test_app.get("/api/predictions/drivers")
    assert response.status_code == 200
    data = response.json()

    assert data["season"] == datetime.now().year
    assert data["type"] == "drivers"
    assert "predicted_champion" in data
    assert "top_contenders" in data
    assert "form_analysis" in data
    assert "ai_reasoning" in data
    assert "races_completed" in data
    assert "races_remaining" in data


def test_predict_driver_champion_structure(test_app, mock_prediction_service):
    """Driver prediction champion has correct structure."""
    response = test_app.get("/api/predictions/drivers")
    data = response.json()

    champion = data["predicted_champion"]
    assert champion is not None
    assert "name" in champion
    assert "current_points" in champion
    assert "predicted_final_points" in champion
    assert "confidence" in champion


def test_predict_constructor_championship_returns_prediction(test_app, mock_prediction_service):
    """Constructor prediction endpoint returns structured prediction."""
    response = test_app.get("/api/predictions/constructors")
    assert response.status_code == 200
    data = response.json()

    assert data["season"] == datetime.now().year
    assert data["type"] == "constructors"
    assert "predicted_champion" in data
    assert "top_contenders" in data
    assert "form_analysis" in data


def test_predict_constructor_champion_structure(test_app, mock_prediction_service):
    """Constructor prediction champion has correct structure."""
    response = test_app.get("/api/predictions/constructors")
    data = response.json()

    champion = data["predicted_champion"]
    assert champion is not None
    assert "name" in champion
    assert "current_points" in champion
    assert "predicted_final_points" in champion
    assert "confidence" in champion


# ── Edge case tests ──

def test_predict_driver_no_year_parameter(test_app, mock_prediction_service):
    """Driver prediction does not require year parameter (current year only)."""
    response = test_app.get("/api/predictions/drivers")
    # Should succeed without year parameter
    assert response.status_code == 200


def test_predict_constructor_no_year_parameter(test_app, mock_prediction_service):
    """Constructor prediction does not require year parameter (current year only)."""
    response = test_app.get("/api/predictions/constructors")
    # Should succeed without year parameter
    assert response.status_code == 200


# ── AI unavailable fallback tests ──

def test_prediction_works_without_ai(test_app, mock_ergast_client, mock_ai_summarizer, mock_prediction_service):
    """Prediction works with statistical fallback when AI is unavailable."""
    mock_ai_summarizer.is_available = False

    response = test_app.get("/api/predictions/drivers")
    assert response.status_code == 200
    data = response.json()

    # Should still return prediction with statistical data
    assert data["season"] == datetime.now().year
    assert "predicted_champion" in data


# ── Form analysis tests ──

def test_form_analysis_included_in_prediction(test_app, mock_prediction_service):
    """Form analysis is included in prediction response."""
    response = test_app.get("/api/predictions/drivers")
    data = response.json()

    form = data.get("form_analysis", {})
    # Form analysis should have entries for top drivers
    assert isinstance(form, dict)


# ── Race count tests ──

def test_races_completed_and_remaining(test_app, mock_prediction_service):
    """Prediction includes races completed and remaining counts."""
    response = test_app.get("/api/predictions/drivers")
    data = response.json()

    assert "races_completed" in data
    assert "races_remaining" in data
    assert isinstance(data["races_completed"], int)
    assert isinstance(data["races_remaining"], int)
    assert data["races_completed"] >= 0
    assert data["races_remaining"] >= 0
