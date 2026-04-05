"""Shared test fixtures and sample data for F1 Assistant tests."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient


def pytest_addoption(parser):
    """Add custom CLI options for e2e tests."""
    parser.addoption("--target", default="http://localhost:8000", help="Base URL of running server")


# ── Sample race data (realistic Ergast response) ──

SAMPLE_RACE_DATA = {
    "season": "2024",
    "round": 1,
    "race_name": "Bahrain Grand Prix",
    "circuit": "Bahrain International Circuit",
    "date": "2024-03-02",
    "location": {"locality": "Sakhir", "country": "Bahrain"},
    "results": [
        {
            "position": 1,
            "driver_code": "VER",
            "driver_name": "Max Verstappen",
            "constructor": "Red Bull",
            "points": 26.0,
            "grid": 1,
            "laps": 57,
            "status": "Finished",
            "time": "1:23:45.123",
        },
        {
            "position": 2,
            "driver_code": "HAM",
            "driver_name": "Lewis Hamilton",
            "constructor": "Mercedes",
            "points": 18.0,
            "grid": 3,
            "laps": 57,
            "status": "Finished",
            "time": "+5.432",
        },
        {
            "position": 3,
            "driver_code": "LEC",
            "driver_name": "Charles Leclerc",
            "constructor": "Ferrari",
            "points": 15.0,
            "grid": 2,
            "laps": 57,
            "status": "Finished",
            "time": "+10.789",
        },
    ],
}

SAMPLE_SCHEDULE = [
    {"round": 1, "race_name": "Bahrain Grand Prix", "circuit": "Bahrain International Circuit", "date": "2024-03-02"},
    {"round": 2, "race_name": "Saudi Arabian Grand Prix", "circuit": "Jeddah Corniche Circuit", "date": "2024-03-09"},
]

SAMPLE_DRIVER_STANDINGS = [
    {"position": 1, "driver_id": "max_verstappen", "driver_name": "Max Verstappen", "constructor": "Red Bull", "points": 575.0, "wins": 19},
    {"position": 2, "driver_id": "sergio_perez", "driver_name": "Sergio Pérez", "constructor": "Red Bull", "points": 285.0, "wins": 2},
]

SAMPLE_CONSTRUCTOR_STANDINGS = [
    {"position": 1, "constructor": "Red Bull", "points": 860.0, "wins": 21},
    {"position": 2, "constructor": "Mercedes", "points": 409.0, "wins": 1},
]

SAMPLE_DRIVER_INFO = {
    "driver_id": "hamilton",
    "code": "HAM",
    "given_name": "Lewis",
    "family_name": "Hamilton",
    "full_name": "Lewis Hamilton",
    "date_of_birth": "1985-01-07",
    "nationality": "British",
    "permanent_number": "44",
    "url": "http://en.wikipedia.org/wiki/Lewis_Hamilton",
}


# ── Mock the AI summarizer to avoid real API calls ──

@pytest.fixture
def mock_ai_summarizer():
    """Mock AISummarizer to return predictable results without calling Qwen."""
    from services.ai_assistant import AISummarizer

    async def fake_summarize(race_text, user_query=""):
        return {
            "summary": "Test summary for the race.",
            "highlights": "Winner: Test Driver; Podium: P2, P3",
            "insights": "Test insight.",
            "answer": "",
        }

    instance = MagicMock(spec=AISummarizer)
    instance.summarize = AsyncMock(side_effect=fake_summarize)
    instance.is_available = True
    instance.model = "coder-model"
    return instance


@pytest.fixture
def mock_ergast_client():
    """Mock ErgastClient to return sample data without network calls."""
    from services.ergast_client import ErgastClient

    instance = MagicMock(spec=ErgastClient)
    instance.get_latest_race = AsyncMock(return_value=dict(SAMPLE_RACE_DATA))
    instance.get_race_by_year_round = AsyncMock(return_value=dict(SAMPLE_RACE_DATA))
    instance.get_season_schedule = AsyncMock(return_value=list(SAMPLE_SCHEDULE))
    instance.get_driver_standings = AsyncMock(return_value=list(SAMPLE_DRIVER_STANDINGS))
    instance.get_constructor_standings = AsyncMock(return_value=list(SAMPLE_CONSTRUCTOR_STANDINGS))
    instance.get_driver_info = AsyncMock(return_value=dict(SAMPLE_DRIVER_INFO))
    instance.get_driver_season_results = AsyncMock(return_value=[])
    return instance


@pytest.fixture
def test_app(mock_ergast_client, mock_ai_summarizer):
    """Create a FastAPI test client with mocked services."""
    import main
    from main import app

    main.ergast_client = mock_ergast_client
    main.ai_summarizer = mock_ai_summarizer

    return TestClient(app)


@pytest.fixture
def sample_race():
    """Return a copy of sample race data."""
    return dict(SAMPLE_RACE_DATA)


@pytest.fixture
def sample_schedule():
    """Return a copy of sample schedule."""
    return list(SAMPLE_SCHEDULE)
