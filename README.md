# F1 Race Assistant

AI-powered Formula 1 dashboard with race summaries, standings, and a smart chat assistant.

## Features

- **Latest Race** — AI-generated summaries with real-time data, podium cards, and highlights
- **Browse Seasons** — Explore any season's race calendar with inline AI summaries
- **Standings** — Driver and Constructor championship tables for any year
- **Reminders** — Set email notifications for upcoming races
- **🤖 AI Assistant Chat** — Free-form F1 Q&A with verified data, web search fallback, and conversation history
- **Driver Pages** — Clickable driver profiles with season results
- **Circuit Pages** — Track info with recent race results
- **Account** — User profiles, favorite drivers, and reminder management

## Quick Start

### Option A: Docker (Recommended)

```bash
docker compose up --build
```

Open **`http://localhost:8000`** in your browser.

### Option B: Local Python

```bash
# Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open **`http://localhost:8000`** for the production build or **`http://localhost:5173`** for the dev server.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.12 + FastAPI (async) |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **Database** | PostgreSQL 18 (asyncpg + SQLAlchemy) |
| **AI** | Qwen via OpenAI-compatible endpoint |
| **External API** | Jolpica-F1 (Ergast mirror at api.jolpi.ca) |
| **Containerisation** | Docker + Docker Compose |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | React SPA |
| GET | `/health` | Health check |
| GET | `/api/races/latest` | AI race summary |
| GET | `/api/races/latest/results` | Basic race results |
| GET | `/api/races/{year}/{round}` | AI summary for specific race |
| GET | `/api/races/{year}/{round}/results` | Basic results + circuit info |
| GET | `/api/seasons/{year}/schedule` | Season race schedule |
| GET | `/api/standings/drivers?year=X` | Driver standings |
| GET | `/api/standings/constructors?year=X` | Constructor standings |
| GET | `/api/drivers/{driver_id}` | Driver profile + results |
| GET | `/api/circuits/{circuit_id}` | Circuit info + recent results |
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login → JWT |
| GET/PUT | `/api/users/me` | Current user profile |
| GET/POST/DELETE | `/api/users/me/favorites` | Driver favorites |
| GET/POST/PUT/DELETE | `/api/reminders` | Race reminders |
| GET/POST/DELETE | `/api/chat/sessions` | Chat session management |
| POST | `/api/chat/sessions/{id}/generate` | Generate AI chat response |

## Project Structure

```
lab9/
├── config.py                  # Configuration constants
├── main.py                    # FastAPI application (17+ endpoints)
├── demo.py                    # CLI demo script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Multi-stage build (Node.js + Python)
├── docker-compose.yml         # postgres + f1-assistant
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx            # Main app with routing
│   │   ├── types/api.ts       # TypeScript type definitions
│   │   ├── services/api.ts    # API service layer (fetch)
│   │   ├── contexts/AuthContext.tsx  # Auth state management
│   │   ├── components/        # Layout, tabs
│   │   └── pages/             # Route-level pages
│   └── vite.config.ts
├── db/
│   ├── database.py            # Async engine, session, init_db
│   └── models.py              # User, Favorite, Reminder, RaceCache, ChatSession, ChatMessage
├── database/
│   └── schema.sql             # Raw SQL schema
├── services/
│   ├── ergast_client.py       # 8 methods: races, standings, drivers, circuits
│   ├── data_parser.py         # Raw data → prompt formatter
│   ├── ai_assistant.py        # Qwen LLM summarizer
│   ├── auth.py                # Password hashing (bcrypt), JWT
│   └── scheduler.py           # APScheduler: reminder emails
├── endpoints/
│   ├── auth.py                # POST /api/auth/*
│   ├── users.py               # GET/PUT /api/users/me
│   ├── reminders.py           # GET/POST/PUT/DELETE /api/reminders/*
│   ├── favorites.py           # GET/POST/DELETE /api/users/me/favorites/*
│   └── chat.py                # Chat sessions + AI responses
├── models/
│   ├── schemas.py             # AI response schemas
│   └── reminder_schemas.py    # Reminder schemas
└── tests/
    ├── test_api.py            # 21 unit tests
    ├── test_e2e.py            # 28 e2e tests (58 total passing)
    └── ...
```

## Running Tests

```bash
# Via Docker (recommended)
docker exec lab9-f1-assistant-1 python -m pytest tests/ -v

# All 58 tests pass (30 unit + 28 e2e)
```

## Security

The AI chat endpoint includes multiple security layers:

- **Input sanitization** — Strips control characters, truncates to 2000 chars
- **Rate limiting** — 10 messages per 60 seconds per user
- **Prompt injection protection** — Blocks "ignore instructions" patterns
- **SQL injection prevention** — SQLAlchemy parameterized queries
- **Session ownership** — Users can only access their own chat sessions
- **XSS prevention** — Markdown rendering with element whitelist, no script/iframe

## Data Source

All race data comes from the **Jolpica-F1 API** (`api.jolpi.ca`) — a community-maintained, fully compatible mirror of the legacy Ergast F1 API. The original Ergast API was deprecated at the end of the 2024 season.

## Version Info

**Current Version:** V2 (Full F1 Assistant)

✅ Personal accounts with JWT auth
✅ Race reminders with email scheduler
✅ PostgreSQL database
✅ React frontend with dark theme
✅ AI Assistant chat with verified data
✅ Web search fallback for comprehensive answers
✅ Driver head-to-head pages
✅ Circuit pages with recent results
✅ Favorites system (heart button on driver pages)
✅ All 58 tests passing

**Planned for future:**
- Season Retrospective — AI summary of entire season storylines
- Driver Head-to-Head comparison tool
- Championship Prediction
