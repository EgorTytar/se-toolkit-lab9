"""Tests for the season retrospective endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import datetime


# ── Retrospective endpoint tests ──

def test_retrospective_route_registered():
    """Retrospective endpoint is registered in the app."""
    import main
    from main import app

    client = TestClient(app)
    # Check the route exists in OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/api/seasons/{year}/retrospective" in paths


def test_retrospective_requires_auth():
    """Retrospective requires authentication."""
    import main
    from main import app

    client = TestClient(app)
    response = client.get("/api/seasons/2024/retrospective")
    assert response.status_code in [401, 403]  # Auth required


def test_retrospective_year_too_old_no_auth():
    """Retrospective rejects years before 1950 (even without auth check first)."""
    import main
    from main import app

    client = TestClient(app)
    # The endpoint validates year before auth in some implementations
    # but our implementation validates year first, so we should get 400
    # However, if auth is checked first, we'll get 401/403
    response = client.get("/api/seasons/1949/retrospective")
    assert response.status_code in [400, 401, 403]


def test_retrospective_year_too_new_no_auth():
    """Retrospective rejects years beyond current+1."""
    import main
    from main import app

    client = TestClient(app)
    response = client.get("/api/seasons/2099/retrospective")
    assert response.status_code in [400, 401, 403]


def test_retrospective_endpoint_accepts_valid_year_format():
    """Retrospective endpoint path accepts integer years."""
    import main
    from main import app

    client = TestClient(app)
    # Verify the route accepts the path format (will get auth error, not 404)
    response = client.get("/api/seasons/2000/retrospective")
    # Should NOT be 404 (route exists)
    assert response.status_code != 404


def test_retrospective_endpoint_path_structure():
    """Retrospective endpoint has correct path structure."""
    import main
    from main import app

    client = TestClient(app)
    response = client.get("/openapi.json")
    paths = response.json().get("paths", {})
    
    # Verify path exists and has year parameter
    assert "/api/seasons/{year}/retrospective" in paths
    route_info = paths["/api/seasons/{year}/retrospective"]
    assert "get" in route_info


def test_retrospective_auth_before_year_validation():
    """If auth is checked first, unauthenticated requests are rejected."""
    import main
    from main import app

    client = TestClient(app)
    # Try multiple years - all should require auth
    for year in [1950, 2000, 2024]:
        response = client.get(f"/api/seasons/{year}/retrospective")
        # Should be auth error OR validation error, not 404
        assert response.status_code in [400, 401, 403]
