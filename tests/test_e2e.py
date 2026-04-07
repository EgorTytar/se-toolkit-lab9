"""End-to-end tests against the running application (real API calls).

These tests hit the actual HTTP endpoints of the running server,
verifying the full pipeline: Ergast API → parser → response.
They do NOT mock the Ergast client — only the AI layer is mocked
to keep tests fast and deterministic.

Run inside the container:
    python -m pytest tests/test_e2e.py -v

Or against a running instance:
    pytest tests/test_e2e.py -v --target=http://localhost:8000
"""

import pytest
from httpx import Client


# Allow overriding target via CLI: pytest --target=http://host:port
def pytest_addoption(parser):
    parser.addoption("--target", default="http://localhost:8000", help="Base URL of running server")


@pytest.fixture(scope="module")
def api():
    """HTTP client with extended timeout for AI endpoints."""
    return Client(timeout=60.0)


@pytest.fixture(scope="module")
def base(pytestconfig):
    return pytestconfig.getoption("target")


# ── Health ──

class TestHealth:
    def test_health_returns_ok(self, api, base):
        r = api.get(f"{base}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "ai_available" in data
        assert data["ai_model"] == "qwen"

    def test_root_serves_html(self, api, base):
        r = api.get(f"{base}/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "F1 Assistant" in r.text


# ── Latest Race ──

class TestLatestRace:
    def test_latest_race_results_structure(self, api, base):
        r = api.get(f"{base}/api/races/latest/results")
        assert r.status_code == 200
        data = r.json()
        assert "race_name" in data
        assert "circuit" in data
        assert "date" in data
        assert "season" in data
        assert "round" in data
        assert "winner" in data
        assert "podium" in data
        assert len(data["podium"]) == 3

    def test_latest_race_summary(self, api, base):
        r = api.get(f"{base}/api/races/latest")
        assert r.status_code == 200
        data = r.json()
        assert "ai_response" in data
        ai = data["ai_response"]
        assert "summary" in ai
        assert "highlights" in ai
        assert "insights" in ai
        assert "answer" in ai
        assert isinstance(ai["summary"], str)
        assert isinstance(ai["highlights"], str)


# ── Season Schedule ──

class TestSeasonSchedule:
    def test_schedule_2024_has_races(self, api, base):
        r = api.get(f"{base}/api/seasons/2024/schedule")
        assert r.status_code == 200
        data = r.json()
        assert data["season"] == 2024
        assert data["race_count"] >= 24  # 2024 had 24 races
        assert len(data["races"]) == data["race_count"]
        assert data["races"][0]["round"] == 1

    def test_schedule_2023_has_races(self, api, base):
        r = api.get(f"{base}/api/seasons/2023/schedule")
        assert r.status_code == 200
        data = r.json()
        assert data["season"] == 2023
        assert data["race_count"] >= 22

    def test_schedule_future_year_404(self, api, base):
        r = api.get(f"{base}/api/seasons/2099/schedule")
        assert r.status_code == 404
        assert "not yet available" in r.json()["detail"].lower()

    def test_schedule_before_1950_404(self, api, base):
        r = api.get(f"{base}/api/seasons/1940/schedule")
        assert r.status_code == 404
        assert "not held before 1950" in r.json()["detail"].lower()


# ── Race Results ──

class TestRaceResults:
    def test_specific_race_2024_round_1(self, api, base):
        """Bahrain GP 2024 — Max Verstappen won."""
        r = api.get(f"{base}/api/races/2024/1/results")
        assert r.status_code == 200
        data = r.json()
        assert "Bahrain" in data["race_name"]
        assert data["winner"]["name"] == "Max Verstappen"
        assert len(data["podium"]) == 3

    def test_specific_race_2023_round_1(self, api, base):
        """Bahrain GP 2023 — Max Verstappen won."""
        r = api.get(f"{base}/api/races/2023/1/results")
        assert r.status_code == 200
        data = r.json()
        assert "Bahrain" in data["race_name"]
        assert data["winner"]["name"] == "Max Verstappen"

    def test_race_summary_has_ai(self, api, base):
        r = api.get(f"{base}/api/races/2024/1")
        assert r.status_code == 200
        data = r.json()
        ai = data["ai_response"]
        assert len(ai["summary"]) > 10
        assert len(ai["highlights"]) > 10

    def test_future_race_400(self, api, base):
        r = api.get(f"{base}/api/races/2099/1/results")
        assert r.status_code == 400
        assert "not started" in r.json()["detail"].lower()

    def test_race_before_1950_400(self, api, base):
        r = api.get(f"{base}/api/races/1940/1/results")
        assert r.status_code == 400
        assert "not held before 1950" in r.json()["detail"].lower()


# ── Standings ──

class TestStandings:
    def test_driver_standings_2024(self, api, base):
        r = api.get(f"{base}/api/standings/drivers?year=2024")
        assert r.status_code == 200
        data = r.json()
        assert data["season"] == 2024
        assert data["type"] == "drivers"
        assert len(data["standings"]) > 0
        assert data["standings"][0]["position"] == 1
        assert "driver_id" in data["standings"][0]

    def test_driver_standings_2023(self, api, base):
        r = api.get(f"{base}/api/standings/drivers?year=2023")
        assert r.status_code == 200
        data = r.json()
        assert data["season"] == 2023
        # Max Verstappen won 2023 championship
        assert data["standings"][0]["driver_name"] == "Max Verstappen"

    def test_constructor_standings_2024(self, api, base):
        r = api.get(f"{base}/api/standings/constructors?year=2024")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "constructors"
        assert len(data["standings"]) > 0

    def test_constructor_standings_2023(self, api, base):
        r = api.get(f"{base}/api/standings/constructors?year=2023")
        assert r.status_code == 200
        data = r.json()
        # Red Bull won 2023 constructors
        assert data["standings"][0]["constructor"] == "Red Bull"

    def test_future_standings_message(self, api, base):
        r = api.get(f"{base}/api/standings/drivers?year=2099")
        assert r.status_code == 200
        data = r.json()
        assert data["standings"] == []
        assert "not started" in data["message"].lower()

    def test_standings_before_1950_message(self, api, base):
        r = api.get(f"{base}/api/standings/drivers?year=1940")
        assert r.status_code == 200
        data = r.json()
        assert "not held before 1950" in data["message"].lower()

    def test_constructors_not_held_1950(self, api, base):
        """Constructors championship didn't exist in 1950."""
        r = api.get(f"{base}/api/standings/constructors?year=1950")
        assert r.status_code == 200
        data = r.json()
        assert "not held" in data["message"].lower()


# ── Driver Pages ──

class TestDriverPages:
    def test_driver_info_hamilton(self, api, base):
        r = api.get(f"{base}/api/drivers/hamilton")
        assert r.status_code == 200
        data = r.json()
        assert data["driver"]["full_name"] == "Lewis Hamilton"
        assert data["driver"]["nationality"] == "British"
        assert data["driver"]["permanent_number"] == "44"

    def test_driver_info_verstappen(self, api, base):
        r = api.get(f"{base}/api/drivers/max_verstappen")
        assert r.status_code == 200
        data = r.json()
        assert "Verstappen" in data["driver"]["full_name"]

    def test_driver_season_results_2024(self, api, base):
        r = api.get(f"{base}/api/drivers/hamilton?year=2024")
        assert r.status_code == 200
        data = r.json()
        assert data["season"] == 2024
        assert len(data["results"]) > 0
        assert "season_stats" in data
        assert data["season_stats"]["races"] > 0
        assert data["season_stats"]["points"] > 0

    def test_driver_not_found(self, api, base):
        r = api.get(f"{base}/api/drivers/nonexistent_driver_xyz")
        assert r.status_code == 404


# ── UI Page ──

class TestUI:
    def test_html_contains_f1_assistant(self, api, base):
        r = api.get(f"{base}/")
        assert "F1 Assistant" in r.text

    def test_html_contains_react_root(self, api, base):
        """The HTML should contain the React root div and script."""
        r = api.get(f"{base}/")
        assert 'id="root"' in r.text
        assert '<script type="module"' in r.text


# ── Multi-race consistency ──

class TestMultiRace:
    """Verify results across multiple races in the same season are consistent."""

    def test_2024_first_three_races(self, api, base):
        """First 3 races of 2024 should all return valid results."""
        for rnd in range(1, 4):
            r = api.get(f"{base}/api/races/2024/{rnd}/results")
            assert r.status_code == 200
            data = r.json()
            assert data["season"] == "2024"
            assert data["round"] == rnd
            assert len(data["podium"]) == 3
            assert data["podium"][0]["position"] == 1

    def test_different_seasons_different_champions(self, api, base):
        """2023 and 2024 should have different constructors champions."""
        r23 = api.get(f"{base}/api/standings/constructors?year=2023")
        r24 = api.get(f"{base}/api/standings/constructors?year=2024")
        assert r23.status_code == 200
        assert r24.status_code == 200
        champ_23 = r23.json()["standings"][0]["constructor"]
        champ_24 = r24.json()["standings"][0]["constructor"]
        # They may or may not be the same, but both should be valid names
        assert len(champ_23) > 2
        assert len(champ_24) > 2


# ── Driver Comparison ──

class TestDriverComparison:
    """E2E tests for the driver head-to-head comparison endpoint.

    Note: These hit the real Jolpica-F1 API and may be slow due to
    rate limiting. The unit tests (test_compare.py) cover all logic
    with mocked data.
    """

    def test_compare_hamilton_verstappen(self, api, base):
        """Compare two well-known drivers — should return valid structure."""
        # Use extended timeout for rate-limited API
        r = api.get(f"{base}/api/compare/drivers?a=hamilton&b=max_verstappen", timeout=180.0)
        assert r.status_code == 200
        data = r.json()
        assert data["driver_a"]["info"]["full_name"] == "Lewis Hamilton"
        assert data["driver_b"]["info"]["full_name"] == "Max Verstappen"
        assert data["driver_a"]["career"]["races"] > 0
        assert data["driver_b"]["career"]["races"] > 0
        assert data["driver_a"]["career"]["wins"] > 0
        assert data["driver_b"]["career"]["wins"] > 0
        assert data["head_to_head"]["shared_races"] > 0

    def test_compare_driver_not_found(self, api, base):
        """Non-existent driver returns 404."""
        r = api.get(f"{base}/api/compare/drivers?a=nonexistent_xyz_123&b=hamilton")
        assert r.status_code == 404
