# F1 Race Results Summarizer

AI-powered Formula 1 race summaries using real data from the Ergast API.

## Features

- Fetch and summarize the latest F1 race results
- Query any race by season year and round number
- AI-generated summaries with winner highlights and key insights
- Graceful fallback when no AI API key is configured
- RESTful API via FastAPI
- CLI demo script for easy demonstration

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set your OpenAI API key

For full AI-generated summaries, set your API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Without a key the app still runs — it returns a basic fallback summary.

### 3. Run the FastAPI server

```bash
uvicorn main:app --reload
```

Server starts at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check, shows if AI is available |
| GET | `/api/races/latest` | Summarize the most recent race |
| GET | `/api/races/{year}/{round}` | Summarize a specific race |

### Query parameters

Both race endpoints accept an optional `user_query` string to ask a specific question:

```
GET /api/races/latest?user_query=Who+finished+on+the+podium?
```

### Example request

```bash
curl http://localhost:8000/api/races/latest
```

### Example response

```json
{
  "race_name": "Bahrain Grand Prix",
  "circuit": "Bahrain International Circuit",
  "date": "2024-03-02",
  "season": "2024",
  "round": 1,
  "ai_response": {
    "summary": "Max Verstappen delivered a dominant performance...",
    "highlights": "Winner: Max Verstappen; Podium: Perez, Leclerc",
    "insights": "Red Bull appears highly competitive this season.",
    "answer": ""
  }
}
```

## CLI Demo

Run the demo script to see race summaries in your terminal:

```bash
# Latest race
python demo.py

# Specific race
python demo.py 2024 1

# With a question
python demo.py 2024 1 "Who won the race?"
```

## Project Structure

```
├── config.py                  # Configuration constants
├── main.py                    # FastAPI application
├── demo.py                    # CLI demo script
├── requirements.txt           # Python dependencies
├── services/
│   ├── ergast_client.py       # Ergast API client
│   ├── data_parser.py         # Data → prompt formatter
│   └── ai_assistant.py        # LLM summarizer
└── models/
    └── schemas.py             # Pydantic models
```

## Data Source

All race data comes from the **Jolpica-F1 API** (`api.jolpi.ca`) — a community-maintained, fully compatible mirror of the legacy Ergast F1 API. The original Ergast API was deprecated at the end of the 2024 season.

## Version 1 Scope

This is Version 1 of the F1 Assistant. Core capability: **summarize any completed F1 race** with clear, engaging commentary.

Planned for Version 2: driver/constructor standings, upcoming race previews, free-form Q&A mode.
