# Formula 1 Assistant Application — Implementation Plan

## Product Vision

A Formula 1 assistant that helps fans stay informed about races, results, and standings through clear, engaging AI-generated explanations powered by real-time data from the Ergast API.

---

## Version 1: Race Results Summarizer

### Core Feature

**Summarize any completed F1 race with clear, engaging commentary.**

The user provides a race name (or latest race), and the application fetches real results from the Ergast API and generates a professional race summary with podium highlights and key insights.

This is the single most valuable feature to end-users: they instantly get an easy-to-read breakdown of what happened in a race without parsing raw data.

### Why This Feature?

| Criteria | Assessment |
|----------|-----------|
| User value | High — fans want quick, engaging race recaps |
| Implementation complexity | Medium — single API integration + AI summarization |
| Demonstrable | Yes — fully functional end-to-end flow |

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│   User CLI  │────▶│  Backend API │────▶│   Ergast API     │────▶│   Raw Data  │
│             │◀────│  (FastAPI)   │◀────│  (HTTP GET)      │◀────│   Parsing   │
└─────────────┘     └──────────────┘     └──────────────────┘     └──────┬──────┘
        ▲                                                                │
        │                                                                ▼
        │                                                    ┌──────────────────┐
        │                                                    │  AI Summarizer   │
        │                                                    │  (LLM Prompt)    │
        │                                                    └──────┬───────────┘
        │                                                           │
        └───────────────────────────────────────────────────────────┘
                                 JSON Response
```

### Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend | Python + FastAPI | Lightweight, async-friendly, easy to set up |
| External API | Jolpica-F1 (Ergast-compatible) | Free, no auth required, official Ergast replacement |
| AI Layer | OpenAI-compatible LLM prompt | Structured JSON output per specification |
| CLI / Demo | Simple Python script or curl | Easy to demonstrate |
| Package management | pip + requirements.txt | Standard Python ecosystem |
| Containerisation | Docker + Docker Compose | Reproducible, one-command deployment |

### Docker Containerisation

A `Dockerfile` and `docker-compose.yml` will be added so the app runs with a single `docker compose up`.

#### Dockerfile

- Multi-stage build: slim Python 3.12 base image
- Non-root user for security
- `OPENAI_API_KEY` passed as an environment variable at runtime
- Exposes port 8000, runs uvicorn with `--host 0.0.0.0`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

- Service: `f1-assistant`
- Port mapping: `8000:8000`
- Environment: `OPENAI_API_KEY` loaded from a `.env` file
- Health check against `/health` endpoint

```yaml
services:
  f1-assistant:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

#### .dockerignore

Excludes unnecessary files from the build context:

```
__pycache__/
*.pyc
.env
.git/
.vscode/
PLAN.md
```

#### Updated project structure

```
lab9/
├── PLAN.md                 # This file
├── requirements.txt        # Dependencies
├── README.md              # Setup and usage instructions
├── config.py              # Configuration (API URLs, model settings)
├── main.py                # FastAPI application entry point
├── demo.py                # CLI demonstration script
├── Dockerfile             # Container image definition
├── docker-compose.yml     # One-command deployment
├── .dockerignore          # Build context exclusions
├── .env.example           # Template for environment variables
├── services/
│   ├── __init__.py
│   ├── ergast_client.py   # Ergast API client
│   ├── ai_assistant.py    # LLM prompt builder & response handler
│   └── data_parser.py     # Raw data → structured format
└── models/
    └── schemas.py         # Pydantic request/response models
```

### Data Flow

1. User requests race results (e.g., "2024 Bahrain Grand Prix" or "latest race")
2. Backend calls Ergast API to fetch race data
3. Raw results parsed and formatted
4. Data sent to AI prompt per the defined system prompt
5. JSON response returned to user

### Jolpica-F1 API Endpoints Used

The original Ergast API was deprecated end of 2024. We use the Jolpica-F1 community mirror (`api.jolpi.ca`), which is fully API-compatible.

```
# Latest race
https://api.jolpi.ca/ergast/f1/current/last/results.json

# Specific race by year and round
https://api.jolpi.ca/ergast/f1/{year}/{round}/results.json

# Race schedule (for previews)
https://api.jolpi.ca/ergast/f1/{year}.json
```

### Output Format (per specification)

```json
{
  "summary": "Short race summary (3-5 sentences)",
  "highlights": "Winner and podium finishers",
  "insights": "Optional key observations",
  "answer": "Optional direct answer to user question"
}
```

### Project Structure

```
lab9/
├── PLAN.md                 # This file
├── requirements.txt        # Dependencies
├── README.md              # Setup and usage instructions
├── config.py              # Configuration (API URLs, model settings)
├── main.py                # FastAPI application entry point
├── services/
│   ├── __init__.py
│   ├── ergast_client.py   # Ergast API client
│   ├── ai_assistant.py    # LLM prompt builder & response handler
│   └── data_parser.py     # Raw data → structured format
├── models/
│   └── schemas.py         # Pydantic request/response models
└── demo.py                # CLI demonstration script
```

### Implementation Steps (Version 1)

#### Step 1: Project Setup
- Initialize Python project structure
- Install dependencies: `fastapi`, `uvicorn`, `httpx`, `pydantic`, `openai`
- Create base FastAPI app with health endpoint

#### Step 2: Ergast API Client
- Implement async HTTP client for Ergast API
- Methods: `get_latest_race()`, `get_race_by_year_round(year, round)`
- Error handling for network failures and empty responses
- Parse JSON response into structured Python objects

#### Step 3: Data Parser
- Convert Ergast response to clean format:
  ```
  Race: {race_name}
  Circuit: {circuit_name}
  Date: {date}

  Results:
  1. {driver} ({constructor}) - {points} points
  2. ...
  ```
- Handle edge cases: DNFs, disqualifications, missing data

#### Step 4: AI Summarizer
- Build system prompt per specification (tone, rules, format)
- Construct user prompt with formatted race data
- Call LLM and validate JSON response
- Handle failures gracefully (fallback summary if AI unavailable)

#### Step 5: API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/races/latest` | Summarize the most recent race |
| GET | `/api/races/{year}/{round}` | Summarize a specific race |

Response for both:
```json
{
  "race_name": "...",
  "circuit": "...",
  "date": "...",
  "ai_response": {
    "summary": "...",
    "highlights": "...",
    "insights": "...",
    "answer": ""
  }
}
```

#### Step 6: Demo Script
- CLI script (`demo.py`) that:
  - Fetches and summarizes the latest race
  - Prints formatted output to console
  - Optionally accepts a race query as argument

#### Step 7: Docker Containerisation
- Create `Dockerfile` with slim Python image, non-root user
- Create `docker-compose.yml` with env var support and health check
- Create `.dockerignore` to keep build context lean
- Create `.env.example` as a template for API keys
- Test: `docker compose up` → server responds on `localhost:8000`

#### Step 8: Testing & Polish
- Test with multiple races across different seasons
- Verify JSON output is always valid
- Handle edge cases (canceled races, partial data)
- Add error messages for invalid inputs

---

## Version 2: Full F1 Assistant

### Additional Features

| Feature | Description |
|---------|-------------|
| **Driver Standings** | Show current championship standings with AI analysis |
| **Constructor Standings** | Team championship overview |
| **Upcoming Race Preview** | Generate preview for next scheduled race |
| **Q&A Mode** | Answer specific user questions about a race |
| **Season Retrospective** | Summarize an entire season's key storylines |

### Extended Architecture

```
Version 1 +
├── services/
│   ├── standings_client.py   # Standings data fetcher
│   ├── preview_generator.py  # Upcoming race previews
│   └── qa_handler.py         # Question answering logic
├── endpoints/
│   ├── standings.py          # /api/standings/driver, /api/standings/constructor
│   └── preview.py            # /api/races/next
└── web_ui/                   # Optional: simple web frontend
    └── index.html
```

### New Endpoints (Version 2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/standings/driver/{year}` | Driver championship standings |
| GET | `/api/standings/constructor/{year}` | Constructor championship standings |
| GET | `/api/races/next` | Preview of upcoming race |
| POST | `/api/ask` | Free-form Q&A about race data |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ergast API downtime | High | Cache last successful response |
| LLM rate limits | Medium | Fallback to template-based summary |
| Invalid JSON from LLM | Medium | Retry with stricter prompt, or parse gracefully |
| Missing race data | Low | Return clear message to user |

---

## Demo Script

```
Option A — Local Python:
1. pip install -r requirements.txt
2. uvicorn main:app --reload
3. curl http://localhost:8000/api/races/latest

Option B — Docker (recommended):
1. docker compose up --build
2. curl http://localhost:8000/api/races/latest

Either way:
3. python demo.py latest        → CLI summary
4. python demo.py 2024 1        → Specific race
5. Show JSON response structure → Validate all fields present
6. Demonstrate error handling   → Invalid race → graceful message
```

---

## Setup Instructions (for README)

```bash
# Option A — Local Python
pip install -r requirements.txt
uvicorn main:app --reload
curl http://localhost:8000/api/races/latest

# Option B — Docker (one command)
cp .env.example .env   # add OPENAI_API_KEY if desired
docker compose up --build
curl http://localhost:8000/api/races/latest

# CLI demo
python demo.py latest
```

---

## Success Criteria

- [ ] Application fetches real data from Ergast API
- [ ] AI generates structured JSON summary per specification
- [ ] Response includes summary, highlights, and insights
- [ ] Error handling works for invalid inputs
- [ ] Demo runs without errors for review
- [ ] No hallucinated data in any response
