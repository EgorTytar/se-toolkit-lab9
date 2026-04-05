"""Tests for the AI summarizer service (fallback mode)."""

from services.ai_assistant import AISummarizer
from config import QWEN_API_KEY


def test_fallback_summary_when_no_api_key(monkeypatch):
    """Test fallback summary when QWEN_API_KEY is empty."""
    from config import QWEN_API_KEY as original_key
    import config

    # Temporarily override the module-level constant
    monkeypatch.setattr(config, "QWEN_API_KEY", "")

    summarizer = AISummarizer()
    summarizer._available = False

    result = summarizer._fallback_summary(
        "Race: Bahrain Grand Prix\nCircuit: Bahrain\nDate: 2024-03-02\n\nResults:\n1. Max Verstappen (Red Bull) - 25 points\n2. Lewis Hamilton (Mercedes) - 18 points"
    )

    assert result["summary"] == "Race results for the Bahrain Grand Prix are in. 1. Max Verstappen (Red Bull) - 25 points took the top spot."
    assert "Max Verstappen" in result["highlights"]
    assert "Lewis Hamilton" in result["highlights"]
    assert result["answer"] == ""


def test_summarizer_available_when_key_set():
    """Test that summarizer is available when key is configured."""
    summarizer = AISummarizer()
    assert summarizer.is_available is True


def test_fallback_handles_missing_race_name():
    """Test fallback when race name is missing."""
    summarizer = AISummarizer()

    result = summarizer._fallback_summary(
        "Race: Unknown\nCircuit: Unknown\nDate: Unknown\n\nResults:\nNo results available."
    )

    assert "Unknown" in result["summary"]
    assert "No podium data" in result["highlights"]


def test_fallback_with_no_results():
    """Test fallback when no results are provided."""
    summarizer = AISummarizer()

    result = summarizer._fallback_summary("Race: Test GP\nResults:\nNo results available.")

    assert "No results available" not in result["summary"]
    assert result["answer"] == ""


def test_fallback_extracts_correct_winner():
    """Test that the correct winner is extracted from results."""
    summarizer = AISummarizer()

    result = summarizer._fallback_summary(
        "Race: Monaco GP\nResults:\n1. Charles Leclerc (Ferrari) - 25 points\n2. Max Verstappen (Red Bull) - 18 points\n3. Lando Norris (McLaren) - 15 points"
    )

    assert "Charles Leclerc" in result["summary"]
    assert "Charles Leclerc" in result["highlights"]
    assert "Max Verstappen" in result["highlights"]
    assert "Lando Norris" in result["highlights"]
