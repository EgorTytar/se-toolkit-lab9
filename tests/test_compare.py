"""Unit tests for the driver comparison endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

# Sample driver data for mocking
SAMPLE_DRIVER_INFO_HAM = {
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

SAMPLE_DRIVER_INFO_VER = {
    "driver_id": "max_verstappen",
    "code": "VER",
    "given_name": "Max",
    "family_name": "Verstappen",
    "full_name": "Max Verstappen",
    "date_of_birth": "1997-09-30",
    "nationality": "Dutch",
    "permanent_number": "1",
    "url": "http://en.wikipedia.org/wiki/Max_Verstappen",
}

# Sample season results (simplified)
SAMPLE_HAM_2024 = [
    {"season": 2024, "round": 1, "race_name": "Bahrain GP", "date": "2024-03-02",
     "position": "7", "grid": 7, "points": 6.0, "status": "Finished",
     "constructor": "Mercedes", "constructor_id": "mercedes"},
    {"season": 2024, "round": 2, "race_name": "Saudi Arabian GP", "date": "2024-03-09",
     "position": "9", "grid": 8, "points": 2.0, "status": "Finished",
     "constructor": "Mercedes", "constructor_id": "mercedes"},
]

SAMPLE_VER_2024 = [
    {"season": 2024, "round": 1, "race_name": "Bahrain GP", "date": "2024-03-02",
     "position": "1", "grid": 1, "points": 25.0, "status": "Finished",
     "constructor": "Red Bull", "constructor_id": "red_bull"},
    {"season": 2024, "round": 2, "race_name": "Saudi Arabian GP", "date": "2024-03-09",
     "position": "1", "grid": 1, "points": 26.0, "status": "Finished",
     "constructor": "Red Bull", "constructor_id": "red_bull"},
]

SAMPLE_STANDINGS_2024 = [
    {"position": 1, "driver_id": "max_verstappen", "driver_name": "Max Verstappen",
     "constructor": "Red Bull", "points": 437.0, "wins": 9},
    {"position": 4, "driver_id": "hamilton", "driver_name": "Lewis Hamilton",
     "constructor": "Mercedes", "points": 223.0, "wins": 2},
]


def _make_mock_ergast():
    """Create a mocked ErgastClient with comparison-appropriate data."""
    from services.ergast_client import ErgastClient
    instance = MagicMock(spec=ErgastClient)
    instance.get_driver_info = AsyncMock(side_effect=lambda did: {
        "hamilton": dict(SAMPLE_DRIVER_INFO_HAM),
        "max_verstappen": dict(SAMPLE_DRIVER_INFO_VER),
    }.get(did, None) or (_ for _ in ()).throw(ValueError(f"Driver '{did}' not found")))
    instance.get_driver_all_results = AsyncMock(side_effect=lambda did: {
        "hamilton": list(SAMPLE_HAM_2024),
        "max_verstappen": list(SAMPLE_VER_2024),
    }.get(did, []))
    instance.get_driver_standings = AsyncMock(return_value=list(SAMPLE_STANDINGS_2024))
    return instance


@pytest.fixture
def mock_ergast():
    return _make_mock_ergast()


@pytest.fixture
def compare_test_app(mock_ergast):
    """Create test app with mocked ergast client for comparison endpoint."""
    import main
    from main import app
    # Replace the compare endpoint's ergast client too
    import endpoints.compare
    endpoints.compare.ergast_client = mock_ergast
    return TestClient(app)


class TestCompareDriversUnit:
    """Unit tests for GET /api/compare/drivers with mocked ErgastClient."""

    def test_compare_returns_valid_structure(self, compare_test_app, mock_ergast):
        """Comparison returns expected data structure."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        assert r.status_code == 200
        data = r.json()
        assert "driver_a" in data
        assert "driver_b" in data
        assert "head_to_head" in data
        assert "info" in data["driver_a"]
        assert "career" in data["driver_a"]
        assert "info" in data["driver_b"]
        assert "career" in data["driver_b"]

    def test_compare_career_stats_has_required_fields(self, compare_test_app, mock_ergast):
        """Career stats contain all required fields."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        for key in ["races", "wins", "podiums", "poles", "points", "championships",
                     "best_finish", "worst_finish", "dnfs", "seasons_competed",
                     "avg_finish", "avg_points", "avg_grid", "win_pct", "podium_pct",
                     "dnf_pct", "teams"]:
            assert key in data["driver_a"]["career"], f"Missing field: {key}"
            assert key in data["driver_b"]["career"], f"Missing field: {key}"

    def test_compare_h2h_has_required_fields(self, compare_test_app, mock_ergast):
        """Head-to-head contains expected fields."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        h2h = data["head_to_head"]
        for key in ["shared_seasons", "shared_races", "driver_a_wins", "driver_b_wins",
                     "draws", "race_details"]:
            assert key in h2h, f"Missing H2H field: {key}"

    def test_compare_driver_not_found_returns_404(self, compare_test_app, mock_ergast):
        """Non-existent driver returns 404."""
        r = compare_test_app.get("/api/compare/drivers?a=nonexistent_xyz&b=hamilton")
        assert r.status_code == 404

    def test_compare_both_drivers_not_found_returns_404(self, compare_test_app, mock_ergast):
        """Both non-existent drivers returns 404."""
        r = compare_test_app.get("/api/compare/drivers?a=abc&b=xyz")
        assert r.status_code == 404

    def test_compare_career_stats_values(self, compare_test_app, mock_ergast):
        """Career stats are computed correctly from sample data."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        # From our sample data: Hamilton has 2 races, 0 wins, 0 podiums
        assert data["driver_a"]["career"]["races"] == 2
        assert data["driver_a"]["career"]["wins"] == 0
        assert data["driver_a"]["career"]["podiums"] == 0
        assert data["driver_a"]["career"]["poles"] == 0
        assert data["driver_a"]["career"]["points"] == 8.0

        # Verstappen: 2 races, 2 wins, 2 podiums, 2 poles
        assert data["driver_b"]["career"]["races"] == 2
        assert data["driver_b"]["career"]["wins"] == 2
        assert data["driver_b"]["career"]["podiums"] == 2
        assert data["driver_b"]["career"]["poles"] == 2
        assert data["driver_b"]["career"]["points"] == 51.0

    def test_compare_average_stats(self, compare_test_app, mock_ergast):
        """Average stats are computed correctly from sample data."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        # Hamilton: avg_finish = (7+9)/2 = 8.0, win_pct = 0%, dnf_pct = 0%
        assert data["driver_a"]["career"]["avg_finish"] == 8.0
        assert data["driver_a"]["career"]["win_pct"] == 0.0
        assert data["driver_a"]["career"]["podium_pct"] == 0.0
        assert data["driver_a"]["career"]["dnf_pct"] == 0.0
        assert data["driver_a"]["career"]["avg_grid"] == 7.5  # (7+8)/2
        assert data["driver_a"]["career"]["avg_points"] == 4.0  # 8/2

        # Verstappen: avg_finish = 1.0, win_pct = 100%
        assert data["driver_b"]["career"]["avg_finish"] == 1.0
        assert data["driver_b"]["career"]["win_pct"] == 100.0
        assert data["driver_b"]["career"]["podium_pct"] == 100.0
        assert data["driver_b"]["career"]["avg_grid"] == 1.0
        assert data["driver_b"]["career"]["avg_points"] == 25.5  # 51/2

    def test_compare_constructor_history(self, compare_test_app, mock_ergast):
        """Constructor history is computed correctly."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        assert len(data["driver_a"]["career"]["teams"]) == 1  # only Mercedes
        assert data["driver_a"]["career"]["teams"][0]["constructor_id"] == "mercedes"
        assert data["driver_a"]["career"]["teams"][0]["races"] == 2
        assert data["driver_a"]["career"]["teams"][0]["years"] == [2024]

        assert len(data["driver_b"]["career"]["teams"]) == 1  # only Red Bull
        assert data["driver_b"]["career"]["teams"][0]["constructor_id"] == "red_bull"

    def test_compare_h2h_verstappen_beats_hamilton(self, compare_test_app, mock_ergast):
        """H2H correctly shows Verstappen winning both races against Hamilton."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=max_verstappen")
        data = r.json()
        h2h = data["head_to_head"]
        assert h2h["shared_races"] == 2
        assert h2h["driver_a_wins"] == 0  # Hamilton
        assert h2h["driver_b_wins"] == 2  # Verstappen
        assert h2h["draws"] == 0
        assert len(h2h["race_details"]) == 2

    def test_compare_same_driver_returns_error(self, compare_test_app, mock_ergast):
        """Comparing a driver with themselves still works (backend allows it)."""
        r = compare_test_app.get("/api/compare/drivers?a=hamilton&b=hamilton")
        assert r.status_code == 200
        data = r.json()
        assert data["driver_a"]["info"]["driver_id"] == "hamilton"
        assert data["driver_b"]["info"]["driver_id"] == "hamilton"
        # H2H should show all draws since it's the same driver
        assert data["head_to_head"]["driver_a_wins"] == data["head_to_head"]["driver_b_wins"]
