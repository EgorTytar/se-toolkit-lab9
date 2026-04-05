"""Tests for the data parser service."""

from services.data_parser import format_race_data


def test_formats_basic_race(sample_race):
    """Test basic race data formatting."""
    result = format_race_data(sample_race)

    assert "Race: Bahrain Grand Prix" in result
    assert "Circuit: Bahrain International Circuit" in result
    assert "Date: 2024-03-02" in result
    assert "Results:" in result
    assert "1. Max Verstappen (Red Bull) - 26.0 points" in result
    assert "2. Lewis Hamilton (Mercedes) - 18.0 points" in result
    assert "3. Charles Leclerc (Ferrari) - 15.0 points" in result


def test_includes_dnf_status(sample_race):
    """Test that non-finished drivers get status tag."""
    sample_race["results"][2]["status"] = "Engine"

    result = format_race_data(sample_race)

    assert "[Engine]" in result


def test_handles_empty_results():
    """Test formatting when no results exist."""
    data = {
        "race_name": "Test Grand Prix",
        "circuit": "Test Circuit",
        "date": "2024-01-01",
        "results": [],
    }
    result = format_race_data(data)

    assert "No results available" in result
    assert "Race: Test Grand Prix" in result


def test_includes_all_positions(sample_race):
    """Test that all driver positions are included."""
    result = format_race_data(sample_race)

    assert "1." in result
    assert "2." in result
    assert "3." in result
    # Should not have 4. since we only have 3 drivers
    assert "4." not in result
