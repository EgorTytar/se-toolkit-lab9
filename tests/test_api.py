"""Tests for FastAPI API endpoints."""

import pytest
from tests.conftest import SAMPLE_RACE_DATA, SAMPLE_SCHEDULE, SAMPLE_DRIVER_STANDINGS


# ── Health endpoint ──

def test_health_check(test_app):
    """Health endpoint returns ok status."""
    response = test_app.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ai_available" in data
    assert data["ai_model"] == "qwen"


# ── Root endpoint ──

def test_root_serves_html(test_app):
    """Root endpoint serves the HTML page."""
    response = test_app.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ── Latest race endpoints ──

def test_latest_race_results(test_app):
    """Latest race basic results endpoint returns structured data."""
    response = test_app.get("/api/races/latest/results")
    assert response.status_code == 200
    data = response.json()
    assert data["race_name"] == "Bahrain Grand Prix"
    assert data["circuit"] == "Bahrain International Circuit"
    assert data["total_drivers"] == 3
    assert data["winner"]["name"] == "Max Verstappen"
    assert len(data["podium"]) == 3


def test_latest_race_summary(test_app):
    """Latest race summary endpoint returns AI response."""
    response = test_app.get("/api/races/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["race_name"] == "Bahrain Grand Prix"
    assert data["season"] == "2024"
    assert data["round"] == 1
    assert "ai_response" in data
    assert "summary" in data["ai_response"]
    assert "highlights" in data["ai_response"]
    assert "insights" in data["ai_response"]
    assert "answer" in data["ai_response"]


def test_latest_race_with_user_query(test_app):
    """Latest race summary accepts user_query parameter."""
    response = test_app.get("/api/races/latest?user_query=Who+won?")
    assert response.status_code == 200
    data = response.json()
    assert data["ai_response"]["summary"] == "Test summary for the race."


# ── Season schedule endpoint ──

def test_season_schedule(test_app):
    """Season schedule returns list of races."""
    response = test_app.get("/api/seasons/2024/schedule")
    assert response.status_code == 200
    data = response.json()
    assert data["season"] == 2024
    assert data["race_count"] == 2
    assert len(data["races"]) == 2
    assert data["races"][0]["race_name"] == "Bahrain Grand Prix"


def test_season_schedule_future_year(test_app):
    """Future season returns 404 with friendly message."""
    response = test_app.get("/api/seasons/2099/schedule")
    assert response.status_code == 404
    data = response.json()
    assert "not yet available" in data["detail"].lower()


def test_season_schedule_before_1950(test_app):
    """Season before 1950 returns 404 with friendly message."""
    response = test_app.get("/api/seasons/1940/schedule")
    assert response.status_code == 404
    data = response.json()
    assert "not held before 1950" in data["detail"].lower()


# ── Race results endpoint ──

def test_race_results_by_year_round(test_app):
    """Race results by year and round returns structured data."""
    response = test_app.get("/api/races/2024/1/results")
    assert response.status_code == 200
    data = response.json()
    assert data["race_name"] == "Bahrain Grand Prix"
    assert data["podium"][0]["name"] == "Max Verstappen"


def test_race_summary_by_year_round(test_app):
    """Race summary by year and round returns AI response."""
    response = test_app.get("/api/races/2024/1")
    assert response.status_code == 200
    data = response.json()
    assert data["race_name"] == "Bahrain Grand Prix"
    assert data["ai_response"]["summary"] == "Test summary for the race."


def test_race_future_year(test_app):
    """Future race returns error with friendly message."""
    response = test_app.get("/api/races/2099/1/results")
    assert response.status_code == 400
    data = response.json()
    assert "not started" in data["detail"].lower()


def test_race_before_1950(test_app):
    """Race before 1950 returns error with friendly message."""
    response = test_app.get("/api/races/1940/1/results")
    assert response.status_code == 400
    data = response.json()
    assert "not held before 1950" in data["detail"].lower()


# ── Standings endpoints ──

def test_driver_standings(test_app):
    """Driver standings returns list of drivers."""
    response = test_app.get("/api/standings/drivers?year=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["season"] == 2024
    assert data["type"] == "drivers"
    assert len(data["standings"]) == 2
    assert data["standings"][0]["driver_name"] == "Max Verstappen"


def test_constructor_standings(test_app):
    """Constructor standings returns list of teams."""
    response = test_app.get("/api/standings/constructors?year=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "constructors"
    assert data["standings"][0]["constructor"] == "Red Bull"


def test_driver_standings_future_year(test_app):
    """Future year driver standings returns message instead of error."""
    response = test_app.get("/api/standings/drivers?year=2099")
    assert response.status_code == 200
    data = response.json()
    assert data["standings"] == []
    assert "not started" in data["message"].lower()


def test_constructor_standings_future_year(test_app):
    """Future year constructor standings returns message instead of error."""
    response = test_app.get("/api/standings/constructors?year=2099")
    assert response.status_code == 200
    data = response.json()
    assert "not started" in data["message"].lower()


def test_standings_before_1950(test_app):
    """Standings before 1950 returns friendly message."""
    response = test_app.get("/api/standings/drivers?year=1940")
    assert response.status_code == 200
    data = response.json()
    assert "not held before 1950" in data["message"].lower()


# ── Driver info endpoint ──

def test_driver_info(test_app):
    """Driver info endpoint returns driver profile."""
    response = test_app.get("/api/drivers/hamilton")
    assert response.status_code == 200
    data = response.json()
    assert data["driver"]["full_name"] == "Lewis Hamilton"
    assert data["driver"]["driver_id"] == "hamilton"


def test_driver_info_with_season(test_app, mock_ergast_client):
    """Driver info with season returns results and stats."""
    mock_ergast_client.get_driver_season_results.return_value = [
        {"round": 1, "race_name": "Bahrain GP", "circuit": "Bahrain", "date": "2024-03-02",
         "position": "1", "grid": 1, "points": 25.0, "status": "Finished"},
    ]

    response = test_app.get("/api/drivers/hamilton?year=2024")
    assert response.status_code == 200
    data = response.json()
    assert "season" in data
    assert data["season"] == 2024


# ── Error handling ──

def test_404_for_unknown_route(test_app):
    """Unknown routes return 404."""
    response = test_app.get("/api/nonexistent")
    assert response.status_code == 404


def test_invalid_year_range(test_app):
    """Year outside valid range returns appropriate error."""
    response = test_app.get("/api/races/1800/1")
    assert response.status_code == 400

    response = test_app.get("/api/races/2099/1/results")
    assert response.status_code == 400
