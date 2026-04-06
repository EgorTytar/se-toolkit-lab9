# Formula 1 Assistant Application — Implementation Plan

## Product Vision

A Formula 1 assistant that helps fans stay informed about races, results, and standings through clear, engaging AI-generated explanations powered by real-time data from the Ergast API.

---

## Version 1 Plan: Race Results Summarizer

### Core Feature

**Summarize any completed F1 race with clear, engaging commentary.**

The user provides a race name (or latest race), and the application fetches real results from the Ergast API and generates a professional race summary with podium highlights and key insights.

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
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS | Type-safe, component-based UI, fast builds |
| External API | Jolpica-F1 (Ergast-compatible) | Free, no auth required, official Ergast replacement |
| AI Layer | Qwen (via OpenAI-compatible endpoint) | Structured JSON output, cost-effective |
| CLI / Demo | Simple Python script or curl | Easy to demonstrate |
| Package management | pip + requirements.txt | Standard Python ecosystem |
| Containerisation | Docker + Docker Compose | Reproducible, one-command deployment |

### Docker Containerisation

A `Dockerfile` and `docker-compose.yml` so the app runs with a single `docker compose up`.

#### Dockerfile

- Multi-stage build: slim Python 3.12 base image
- Non-root user for security
- Exposes port 8000, runs uvicorn with `--host 0.0.0.0`

#### docker-compose.yml

- Service: `f1-assistant`
- Port mapping: `8000:8000`
- Health check against `/health` endpoint

#### .dockerignore

```
__pycache__/
*.pyc
.env
.git/
.vscode/
.venv/
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

# Race schedule
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

### Implementation Steps (Version 1)

#### Step 1: Project Setup
- Initialize Python project structure
- Install dependencies: `fastapi`, `uvicorn`, `httpx`, `pydantic`, `openai`
- Create base FastAPI app with health endpoint

#### Step 2: Ergast API Client
- Implement async HTTP client for Ergast API
- Methods: `get_latest_race()`, `get_race_by_year_round(year, round)`, `get_season_schedule(year)`, `get_driver_standings(year)`, `get_constructor_standings(year)`, `get_driver_info(driver_ref)`, `get_driver_season_results(driver_ref, year)`
- Error handling for network failures and empty responses

#### Step 3: Data Parser
- Convert Ergast response to clean AI prompt format
- Handle edge cases: DNFs, disqualifications, missing data

#### Step 4: AI Summarizer
- Build system prompt per specification (tone, rules, format)
- Construct user prompt with formatted race data
- Call LLM and validate JSON response
- Handle failures gracefully (fallback summary if AI unavailable)

#### Step 5: API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI dashboard |
| GET | `/health` | Health check |
| GET | `/api/races/latest` | Summarize the most recent race |
| GET | `/api/races/latest/results` | Basic results (no AI) |
| GET | `/api/races/{year}/{round}` | Summarize a specific race |
| GET | `/api/races/{year}/{round}/results` | Basic results (no AI) |
| GET | `/api/seasons/{year}/schedule` | Season race schedule |
| GET | `/api/standings/drivers` | Driver championship standings |
| GET | `/api/standings/constructors` | Constructor championship standings |
| GET | `/api/drivers/{driver_id}` | Driver profile and season results |

#### Step 6: Demo Script
- CLI script (`demo.py`) that fetches and summarizes the latest race

#### Step 7: Docker Containerisation
- Dockerfile, docker-compose.yml, .dockerignore

#### Step 8: Testing & Polish
- Unit tests (30) and e2e tests (28)
- Edge cases: canceled races, future races, invalid input
- Dynamic year validation (no hardcoded limits)

---

## Version 1 Results: What Actually Shipped

### ✅ All 8 Steps Completed

| Step | Deliverables |
|------|-------------|
| 1. Project Setup | `config.py`, `requirements.txt`, project structure |
| 2. Ergast API Client | `ergast_client.py` — 6 methods, async, error handling |
| 3. Data Parser | `data_parser.py` — formats race data for AI prompts |
| 4. AI Summarizer | `ai_assistant.py` — Qwen integration with fallback |
| 5. API Endpoints | 10 endpoints across `main.py` |
| 6. Demo Script | `demo.py` — CLI race summary |
| 7. Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example` |
| 8. Testing | 58 tests (30 unit + 28 e2e), all passing |

### ✅ Success Criteria — All Met

- [x] Application fetches real data from Jolpica-F1 API
- [x] AI generates structured JSON summary per specification
- [x] Response includes summary, highlights, and insights
- [x] Error handling works for invalid inputs
- [x] Demo runs without errors
- [x] No hallucinated data in any response
- [x] 30+ automated tests
- [x] Future races handled gracefully with preview mode
- [x] Standings available for past years, friendly message for future years
- [x] Driver detail pages accessible from standings

### 🎁 Shipped Beyond Original V1 Scope

| Feature | Description |
|---------|-------------|
| **Web UI Dashboard** | Single-page HTML app with tabs for Latest Race, Browse Seasons, Standings |
| **Season Browsing** | Year input → full race list → inline expand with AI summary |
| **Driver Standings** | Championship table for any year 1950–present |
| **Constructor Standings** | Team championship table for any year |
| **Driver Detail Pages** | Clickable driver names → profile + season-by-season race results |
| **Future Race Preview** | Races that haven't happened show schedule info + AI-generated preview |
| **Dynamic Year Validation** | Uses `datetime.now().year` — no hardcoded 2030 limit |
| **Hash-Based Routing** | `#/driver/{id}` is bookmarkable |
| **Full Test Suite** | 30 unit tests + 28 e2e tests against real running server |

### 📁 Final Project Structure

```
lab9/
├── config.py                  # Configuration (API URLs, Qwen settings)
├── main.py                    # FastAPI application (10 endpoints)
├── demo.py                    # CLI demonstration script
├── requirements.txt           # Python dependencies
├── requirements-test.txt      # Test dependencies
├── pyproject.toml             # pytest configuration
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # One-command deployment
├── .dockerignore              # Build context exclusions
├── .env.example               # Template for environment variables
├── static/
│   ├── index.html             # Legacy Web UI (replaced by React)
│   └── dist/                  # React build output (served in production)
├── frontend/                  # React frontend (Vite + TypeScript)
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.ts         # Vite build configuration
│   ├── index.html             # React entry point
│   └── src/
│       ├── App.tsx            # Main app component with routing
│       ├── main.tsx           # React entry point
│       ├── index.css          # Tailwind CSS styles
│       ├── types/
│       │   └── api.ts         # TypeScript type definitions
│       ├── services/
│       │   └── api.ts         # API service layer (axios wrappers)
│       ├── contexts/
│       │   └── AuthContext.tsx # Authentication context
│       ├── components/
│       │   ├── Layout.tsx     # Header, footer, navigation
│       │   └── tabs/          # Dashboard tab components
│       │       ├── LatestRaceTab.tsx
│       │       ├── BrowseSeasonsTab.tsx
│       │       ├── StandingsTab.tsx
│       │       └── RemindersTab.tsx
│       └── pages/             # Route page components
│           ├── HomePage.tsx
│           ├── AccountPage.tsx
│           ├── DriverPage.tsx
│           ├── CircuitPage.tsx
│           ├── LoginPage.tsx
│           └── RegisterPage.tsx
├── services/
│   ├── __init__.py
│   ├── ergast_client.py       # Ergast API client (6 methods)
│   ├── ai_assistant.py        # Qwen LLM summarizer
│   └── data_parser.py         # Raw data → prompt formatter
├── models/
│   ├── __init__.py
│   └── schemas.py             # Pydantic models
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared fixtures and mock data
    ├── test_data_parser.py    # Data parser tests (4 tests)
    ├── test_ai_assistant.py   # AI fallback tests (5 tests)
    ├── test_api.py            # API endpoint tests (21 tests)
    └── test_e2e.py            # E2E tests against running server (28 tests)
```

---

## Frontend Migration: React + TypeScript

The frontend has been migrated from a single static HTML file (1,700+ lines) to a modern React + TypeScript application with the following improvements:

### What Changed

| Before (Vanilla HTML/JS) | After (React + TypeScript) |
|--------------------------|----------------------------|
| Single 1,700+ line `static/index.html` | Component-based architecture (20+ files) |
| Manual DOM manipulation | Declarative React components |
| No type safety | Full TypeScript support |
| Browser caching issues | Build-time cache busting with hashed assets |
| Round 3 detail bug (JS scope issue) | Fixed with proper React state management |
| Inline CSS | Tailwind CSS utility classes |
| No routing | React Router with proper URL paths |
| Hard to test | Component-level testing possible |

### React Project Structure

```
frontend/
├── src/
│   ├── App.tsx              # Main app with routing
│   ├── main.tsx             # Entry point
│   ├── index.css            # Tailwind imports
│   ├── types/api.ts         # 20+ TypeScript interfaces
│   ├── services/api.ts      # Axios-based API wrappers
│   ├── contexts/AuthContext.tsx  # Auth state management
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # Header, nav, footer
│   │   └── tabs/            # Dashboard tabs
│   └── pages/               # Route-level pages
│       ├── HomePage.tsx     # Main dashboard
│       ├── AccountPage.tsx  # User profile + favorites + reminders
│       ├── DriverPage.tsx   # Driver detail with favorites
│       ├── CircuitPage.tsx  # Circuit info + recent results
│       ├── LoginPage.tsx
│       └── RegisterPage.tsx
```

### Docker Build Process

The Dockerfile now uses a **multi-stage build**:
1. **Stage 1**: Node.js 20 Alpine builds the React app (`npm run build`)
2. **Stage 2**: Python 3.12 slim copies the build output and serves it via FastAPI

### Features Preserved

✅ All V1 features (race summaries, standings, driver/circuit pages)  
✅ All V2 features (auth, favorites, reminders, account management)  
✅ All 58 tests pass (30 unit + 28 e2e)  
✅ SPA routing with proper 404 for unknown API routes  
✅ Hash-based URLs replaced with proper routes (`/driver/{id}`, `/circuit/{id}`, `/account`)

---

## Version 2 Plan: Full F1 Assistant

Version 1 shipped with more features than originally planned. Version 2 focuses on **deeper engagement** — AI analysis, interactivity, and richer content.

### New V2 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Personal Accounts** | User registration, login, profiles with favorite drivers/teams, saved preferences | Critical |
| **Race Reminders** | Email/push notifications before upcoming races, personalized per user's favorite drivers | Critical |
| **Database (PostgreSQL)** | Persistent storage for users, favorites, reminders, and cached race data | Critical |
| **Season Retrospective** | AI-generated summary of an entire season's storylines, key moments, and championship narrative | High |
| **Upcoming Race Preview** | Detailed AI preview with circuit info, recent form, historical results, and storylines to watch | High |
| **Free-Form Q&A** | Ask any question about F1 — "Who has the most wins at Monaco?" "How did Hamilton do in 2021?" | High |
| **Driver Head-to-Head** | Compare two drivers side-by-side: wins, podiums, points, head-to-head qualifying/race record | Medium |
| **Team Comparison** | Constructor head-to-head with historical data and season-over-season trends | Medium |
| **Circuit Pages** | Track information, lap records, most wins, recent results, layout diagram | Medium |
| **Championship Prediction** | AI-powered championship outcome prediction based on current form and remaining races | Low |
| **Live Race Weekend** | Real-time session results (practice, qualifying, race) during race weekends | Low |

### Architecture Changes

```
Version 2 Architecture
├── database/
│   ├── postgres/              # PostgreSQL service
│   ├── migrations/            # Alembic migrations
│   └── schema.sql             # Initial schema
├── services/
│   ├── auth.py                # User registration, login, JWT
│   ├── profiles.py            # User profiles, favorites, preferences
│   ├── reminders.py           # Scheduled notifications, email/push
│   ├── retrospective.py       # Full season AI retrospective
│   ├── preview.py             # Upcoming race preview generator
│   ├── qa_engine.py           # Free-form Q&A with context
│   ├── comparison.py          # Driver/team head-to-head
│   └── circuit_data.py        # Circuit information & stats
├── endpoints/
│   ├── auth.py                # POST /api/auth/register, /api/auth/login
│   ├── users.py               # GET/PUT /api/users/me, /api/users/me/favorites
│   ├── reminders.py           # GET/POST /api/reminders
│   ├── retrospective.py       # GET /api/seasons/{year}/retrospective
│   ├── preview.py             # GET /api/races/next/preview
│   ├── qa.py                  # POST /api/ask
│   └── compare.py             # GET /api/compare/drivers?a=x&b=y
└── web_ui/
    ├── index.html             # Main dashboard (existing)
    ├── auth.html              # Login/Register pages
    ├── profile.html           # User profile, favorites, settings
    ├── circuit.html           # Circuit detail pages
    └── compare.html           # Driver/team comparison tool
├── docker-compose.yml         # + PostgreSQL service
└── requirements.txt           # + sqlalchemy, psycopg2, jose, passlib
```

### Database Schema (Overview)

```sql
users (
    id, email, password_hash, display_name, created_at, last_login
)

user_favorites (
    user_id, driver_id, constructor_id, created_at
)

reminders (
    id, user_id, race_round, race_year, notify_before_hours,
    enabled, method (email/push), created_at
)

race_cache (
    year, round, race_name, circuit, date, results_json,
    ai_summary_json, cached_at
)
```

### New Endpoints (Version 2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login (returns JWT) |
| GET | `/api/users/me` | Current user profile |
| PUT | `/api/users/me` | Update profile |
| GET | `/api/users/me/favorites` | Get favorite drivers/teams |
| POST | `/api/users/me/favorites` | Add favorite |
| DELETE | `/api/users/me/favorites/{id}` | Remove favorite |
| GET | `/api/reminders` | List user's race reminders |
| POST | `/api/reminders` | Create a reminder |
| DELETE | `/api/reminders/{id}` | Delete a reminder |
| GET | `/api/seasons/{year}/retrospective` | AI summary of entire season |
| GET | `/api/races/next/preview` | Preview of next scheduled race |
| POST | `/api/ask` | Free-form Q&A about F1 data |
| GET | `/api/compare/drivers` | Head-to-head driver comparison |
| GET | `/api/compare/constructors` | Head-to-head team comparison |
| GET | `/api/circuits/{circuit_id}` | Circuit information and stats |

### Implementation Order

1. **Database (PostgreSQL)** — foundation for all V2 features: users, favorites, reminders, cache
2. **Personal Accounts** — registration, login (JWT), profiles — unlocks personalized features
3. **Race Reminders** — notification scheduler, email/push integration, user-configured alerts
4. **Upcoming Race Preview** — natural extension of existing future race handling
5. **Season Retrospective** — aggregates all races in a season into AI narrative
6. **Free-Form Q&A** — builds on existing AI summarizer with conversational context
7. **Driver Head-to-Head** — leverages existing driver pages infrastructure
8. **Circuit Pages** — new data from Ergast, new UI section
9. **Team Comparison** — similar to driver comparison
10. **Championship Prediction** — AI-powered predictions
11. **Live Race Weekend** — requires polling or webhook for session updates

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ergast API downtime | High | Cache last successful response in database |
| LLM rate limits | Medium | Fallback to template-based summary |
| Invalid JSON from LLM | Medium | Retry with stricter prompt, or parse gracefully |
| Missing race data | Low | Return clear message to user |
| User data breaches | Critical | Password hashing (bcrypt), JWT expiry, HTTPS |
| Notification spam | Medium | User-configurable limits, unsubscribe option |
| Database migration failures | Medium | Alembic with rollback support |

---

## Demo Script

```
Option A — Local Python:
1. pip install -r requirements.txt
2. uvicorn main:app --reload
3. Open http://localhost:8000

Option B — Docker (recommended):
1. docker compose up --build
2. Open http://localhost:8000

Demo flow:
1. Latest Race tab → auto-loaded race summary
2. Browse Seasons → enter 2024 → click any race → inline AI summary
3. Standings → 2024 → Drivers table → click a driver name → driver page
4. Show error handling → enter year 1940 or 2099 → friendly message
```

---

## Setup Instructions

```bash
# Option A — Local Python
pip install -r requirements.txt
uvicorn main:app --reload

# Option B — Docker (one command)
docker compose up --build

# Run tests
docker exec lab9-f1-assistant-1 python -m pytest tests/ -v

# CLI demo
python demo.py latest
```
