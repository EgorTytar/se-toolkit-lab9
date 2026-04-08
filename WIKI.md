# F1 Race Assistant — Full Project Wiki

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Backend — FastAPI](#5-backend--fastapi)
6. [Backend — Endpoints](#6-backend--endpoints)
7. [Backend — Services](#7-backend--services)
8. [Database](#8-database)
9. [Frontend — React](#9-frontend--react)
10. [Frontend — Components](#10-frontend--components)
11. [Frontend — State Management](#11-frontend--state-management)
12. [AI System](#12-ai-system)
13. [Caching System](#13-caching-system)
14. [Security](#14-security)
15. [Docker & Deployment](#15-docker--deployment)
16. [Testing](#16-testing)
17. [API Reference](#17-api-reference)
18. [Development Guide](#18-development-guide)

---

## 1. Overview

F1 Race Assistant is a full-stack web application that provides Formula 1 fans with:

- **Real-time race data** from the Jolpica-F1 API (Ergast mirror)
- **AI-generated race summaries** via Qwen LLM
- **Season browsing** — explore any F1 season from 1950 to present
- **Driver standings & constructor standings** for any year
- **Driver profiles** with season-by-season results
- **Circuit pages** with recent race history
- **🤖 AI Assistant Chat** — free-form F1 Q&A with verified data + web search
- **📖 Season Retrospective** — AI narratives of entire F1 seasons
- **User accounts** — registration, login, profiles (JWT auth)
- **Favorites** — save favorite drivers
- **Reminders** — set notifications for upcoming races (email + scheduler)
- **⚔️ Driver Comparison** — head-to-head career stats + race-by-race H2H record
- **🔮 Championship Predictions** — AI-powered predictions with form analysis, confidence levels, and contender odds

**Version:** V2 (Full F1 Assistant)
**Tests:** All unit tests passing (see Testing section for details)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              React SPA (Vite + TypeScript)             │   │
│  │  ┌────────┬─────────┬──────────┬────────┬──────────┬─────────┬──────────────┐ │   │
│  │  │Latest  │Browse   │Standings │Remind  │Retrospect│Compare  │Predictions   │ │   │
│  │  │Race    │Seasons  │          │        │ive       │         │              │ │   │
│  │  └────────┴─────────┴──────────┴────────┴──────────┴─────────┴──────────────┘ │   │
│  └──────────────────────┬────────────────────────────────┘   │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTP/JSON
┌─────────────────────────┼────────────────────────────────────┐
│                    Docker Container                           │
│  ┌─────────────────────┴──────────────────────────────────┐   │
│  │           FastAPI Backend (Python 3.12)                │   │
│  │  ┌─────────┬──────────┬────────┬────────┬──────────┬─────────┬──────────────┐ │   │
│  │  │Race API │Standings │Driver  │Chat    │Retro     │Compare  │Predictions   │ │   │
│  │  │Endpoints│Endpoints │Endpoint│Endpoint│Endpoint  │Endpoint │Endpoint      │ │   │
│  │  └─────────┴──────────┴────────┴────────┴──────────┴─────────┴──────────────┘ │   │
│  │  ┌──────────────┬──────────────┬──────────────────┐   │   │
│  │  │Ergast Client │AI Summarizer │Cache Service     │   │   │
│  │  └──────────────┴──────────────┴──────────────────┘   │   │
│  └─────────────────────────┬──────────────────────────────┘   │
└────────────────────────────┼──────────────────────────────────┘
                ┌────────────┴────────────┐
                │                         │
    ┌───────────▼──────────┐  ┌──────────▼───────────┐
    │ PostgreSQL 18        │  │ Jolpica-F1 API       │
    │ (Users, Favorites,   │  │ (https://api.jolpi.ca)│
    │  Reminders, Chats,   │  │ — Real F1 data       │
    │  AI Cache)           │  └──────────────────────┘
    └──────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12 + FastAPI (async) | REST API, async request handling |
| **Frontend** | React 18 + TypeScript + Vite | Component-based UI, type safety |
| **CSS** | Tailwind CSS (v4) | Utility-first dark theme styling |
| **Database** | PostgreSQL 18 (asyncpg + SQLAlchemy) | Persistent storage, async ORM |
| **AI** | Qwen (OpenAI-compatible via Jolpi.ca) | Race summaries, chat, retrospectives |
| **External API** | Jolpica-F1 (Ergast mirror) | Real F1 race data, standings, circuits |
| **Auth** | JWT (python-jose) + bcrypt | Token-based authentication |
| **Scheduler** | APScheduler | Background email reminder checks |
| **Containerization** | Docker + Docker Compose | One-command deployment |
| **Testing** | pytest + httpx | 65 tests (unit + e2e) |
| **Build** | Multi-stage Dockerfile | Node.js builds React, Python serves it |

---

## 4. Project Structure

```
lab9/
├── config.py                  # API URLs, Qwen settings
├── main.py                    # FastAPI app — 17+ endpoints, lifespan, middleware
├── demo.py                    # CLI demo script
├── dependencies.py            # get_current_user() JWT dependency
├── requirements.txt           # Python dependencies
├── requirements-test.txt      # Test dependencies
├── pyproject.toml             # pytest configuration
├── Dockerfile                 # Multi-stage: Node.js (build React) → Python (serve)
├── docker-compose.yml         # postgres + f1-assistant services
├── .dockerignore              # Excludes node_modules, .git, __pycache__
│
├── db/                        # Database layer
│   ├── database.py            # Async engine, session, init_db, close_db
│   └── models.py              # SQLAlchemy models (User, Favorite, Reminder, Chat, AICache)
│
├── database/
│   └── schema.sql             # Raw SQL schema for manual DB setup
│
├── services/                  # Business logic
│   ├── ergast_client.py       # Jolpica-F1 API client (8 methods)
│   ├── ai_assistant.py        # Qwen LLM summarizer + chat
│   ├── data_parser.py         # Raw race data → AI prompt formatter
│   ├── auth.py                # Password hashing (bcrypt), JWT create/verify
│   ├── scheduler.py           # APScheduler: hourly reminder checks, email sending
│   ├── cache_service.py       # AI response caching with TTL
│   └── prediction_service.py  # Championship prediction engine (form + stats + AI)
│
├── endpoints/                 # API route handlers
│   ├── auth.py                # POST /api/auth/register, /api/auth/login
│   ├── users.py               # GET/PUT /api/users/me
│   ├── reminders.py           # GET/POST/PUT/DELETE /api/reminders/*
│   ├── favorites.py           # GET/POST/DELETE /api/users/me/favorites/*
│   ├── chat.py                # Chat sessions + AI response generation
│   ├── retrospective.py       # GET /api/seasons/{year}/retrospective
│   ├── compare.py             # GET /api/compare/drivers — H2H comparison
│   ├── push_notifications.py  # GET/POST /api/push/* — Web push subscriptions
│   └── predictions.py         # GET /api/predictions/* — Championship predictions
│
├── models/                    # Pydantic schemas
│   ├── schemas.py             # AIResponse, RaceSummaryResponse, ErrorResponse
│   ├── auth_schemas.py        # RegisterRequest, LoginRequest, LoginResponse
│   └── reminder_schemas.py    # ReminderCreate, ReminderResponse
│
├── frontend/                  # React TypeScript frontend
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.ts         # Vite + React + Tailwind config
│   ├── index.html             # React entry point
│   └── src/
│       ├── App.tsx            # Main app with routing
│       ├── main.tsx           # React entry point + error boundary
│       ├── index.css          # Tailwind + markdown content styles
│       ├── types/
│       │   └── api.ts         # TypeScript interfaces (20+)
│       ├── services/
│       │   └── api.ts         # API service layer (fetch wrappers)
│       ├── contexts/
│       │   └── AuthContext.tsx # Auth state + JWT management
│       ├── components/
│       │   ├── Layout.tsx      # Header, nav, footer (dark theme)
│       │   └── tabs/           # Dashboard tab components
│       │       ├── LatestRaceTab.tsx
│       │       ├── BrowseSeasonsTab.tsx
│       │       ├── StandingsTab.tsx
│       │       ├── RemindersTab.tsx
│       │       ├── RetrospectiveTab.tsx
│       │       ├── CompareTab.tsx       # ⚔️ Driver H2H comparison
│       │       ├── PredictionsTab.tsx   # 🔮 Championship predictions
│       │       └── ChatTab.tsx
│       └── pages/              # Route-level pages
│           ├── HomePage.tsx    # Main dashboard with tabs
│           ├── AccountPage.tsx # Profile + Favorites + Reminders
│           ├── DriverPage.tsx  # Driver profile + season results
│           ├── CircuitPage.tsx # Circuit info + recent results
│           ├── LoginPage.tsx
│           └── RegisterPage.tsx
│
├── static/
│   └── dist/                  # React build output (served in production)
│
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures, mock data
│   ├── test_api.py            # 21 unit tests for API endpoints
│   ├── test_e2e.py            # 28+ e2e tests against running server
│   ├── test_retrospective.py  # 7 retrospective endpoint tests
│   ├── test_compare.py        # 8 comparison endpoint unit tests
│   ├── test_predictions.py    # 9 championship prediction tests
│   ├── test_push_notifications.py  # 5 push notification tests
│   ├── test_data_parser.py    # 4 data parser tests
│   └── test_ai_assistant.py   # 5 AI fallback tests
│
└── WIKI.md                    # This file
```

---

## 5. Backend — FastAPI

### Application Lifecycle (`main.py`)

```
lifespan(app):
  1. init_db()        → Create all SQLAlchemy tables
  2. start_scheduler() → Start APScheduler for reminders
  3. yield            → Server runs
  4. stop_scheduler() → Stop background scheduler
  5. close_db()       → Dispose database engine
```

### Middleware

| Middleware | Purpose |
|-----------|---------|
| **CORS** | `allow_origins=["*"]` — all origins, methods, headers |
| **NoCache** | Adds `Cache-Control: no-cache` to HTML and asset responses |

### SPA Routing

- `GET /` → Serves `static/dist/index.html` (React SPA)
- `GET /{full_path}` → Catches all non-API routes, serves React SPA
- `GET /api/*` → Raises 404 for unknown API routes (not caught by catch-all)

---

## 6. Backend — Endpoints

### Public Endpoints (no auth required)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Health check (db_healthy, ai_available) | ❌ |
| GET | `/api/races/latest/results` | Basic results (no AI) | ❌ |
| GET | `/api/races/{year}/{round}/results` | Basic results + circuit_id | ❌ |
| GET | `/api/seasons/{year}/schedule` | Season race schedule | ❌ |
| GET | `/api/standings/drivers?year=X` | Driver standings | ❌ |
| GET | `/api/standings/constructors?year=X` | Constructor standings | ❌ |
| GET | `/api/drivers/{driver_id}` | Driver profile + season results | ❌ |
| GET | `/api/circuits/{circuit_id}` | Circuit info + recent results | ❌ |
| GET | `/api/compare/drivers?a=X&b=Y` | Driver head-to-head comparison | ❌ |
| GET | `/api/compare/drivers/search?q=ham` | Search drivers by name/code | ❌ |
| GET | `/api/compare/constructors?a=X&b=Y` | Constructor comparison | ❌ |
| GET | `/api/compare/constructors/search?q=fer` | Search constructors | ❌ |
| POST | `/api/auth/register` | Register user → returns JWT | ❌ |
| POST | `/api/auth/login` | Login → returns JWT | ❌ |

### Authenticated Endpoints (JWT required)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/races/latest` | AI summary of latest race | ✅ |
| GET | `/api/races/{year}/{round}` | AI summary for specific race | ✅ |
| GET | `/api/predictions/drivers` | AI driver championship prediction | ✅ |
| GET | `/api/predictions/constructors` | AI constructor championship prediction | ✅ |
| GET | `/api/seasons/{year}/retrospective` | AI season retrospective | ✅ |
| GET | `/api/users/me` | Current user profile | ✅ |
| PUT | `/api/users/me` | Update profile | ✅ |
| GET | `/api/users/me/favorites/` | Get favorite drivers | ✅ |
| POST | `/api/users/me/favorites/` | Add favorite driver | ✅ |
| DELETE | `/api/users/me/favorites/{id}` | Remove favorite | ✅ |
| GET | `/api/reminders/` | List user's reminders | ✅ |
| POST | `/api/reminders/` | Create reminder | ✅ |
| PUT | `/api/reminders/{id}` | Update reminder | ✅ |
| DELETE | `/api/reminders/{id}` | Delete reminder | ✅ |
| GET | `/api/chat/sessions` | List chat sessions | ✅ |
| POST | `/api/chat/sessions` | Create chat session | ✅ |
| GET | `/api/chat/sessions/{id}` | Get session with messages | ✅ |
| DELETE | `/api/chat/sessions/{id}` | Delete session | ✅ |
| POST | `/api/chat/sessions/{id}/messages` | Save user message | ✅ |
| POST | `/api/chat/sessions/{id}/generate` | Generate AI response | ✅ |
| GET | `/api/seasons/{year}/retrospective` | AI season retrospective | ✅ |

---

## 7. Backend — Services

### `ergast_client.py` — Jolpica-F1 API Client

Async HTTP client wrapping `https://api.jolpi.ca/ergast/f1/`:

| Method | Description |
|--------|-------------|
| `get_latest_race()` | Latest completed race results |
| `get_race_by_year_round(year, round)` | Specific race results |
| `get_season_schedule(year)` | Full season calendar |
| `get_driver_standings(year)` | Driver championship table |
| `get_constructor_standings(year)` | Constructor championship table |
| `get_driver_info(driver_ref)` | Driver profile info |
| `get_driver_season_results(driver_ref, year)` | Driver's season race-by-race |
| `get_circuit_info(circuit_id)` | Circuit details |
| `get_circuit_recent_results(circuit_id)` | Last 5 races at circuit |
| `get_season_races(year)` | Full season race results (all races) |
| `get_driver_all_results(driver_ref)` | All career results (paginated) |
| `get_all_drivers()` | Full driver list for search/autocomplete (cached) |

### `ai_assistant.py` — AI Summarizer

Two modes of operation:

| Method | Purpose | Output |
|--------|---------|--------|
| `summarize(race_text, user_query)` | Race summary (JSON format) | `{summary, highlights, insights, answer}` |
| `chat_response(messages)` | Free-form chat | Plain text |

Configured via `config.py`:
- `QWEN_MODEL`: Model name
- `QWEN_BASE_URL`: API endpoint
- `QWEN_API_KEY`: API key

### `cache_service.py` — AI Response Caching

| Function | Purpose |
|----------|---------|
| `get_cached_response(db, key)` | Returns cached response if valid |
| `cache_response(db, key, data, ttl)` | Stores response with expiration |
| `invalidate_cache(db, key)` | Removes cached entry |

Cache TTLs:
- Race summaries: **24 hours**
- Retrospectives: **12 hours**
- Predictions: **6 hours**
- Default: **6 hours**

### `auth.py` — Authentication

| Function | Purpose |
|----------|---------|
| `hash_password(password)` | bcrypt hashing |
| `verify_password(password, hash)` | bcrypt verification |
| `create_access_token(data)` | JWT creation (python-jose) |
| `decode_access_token(token)` | JWT verification |

### `scheduler.py` — Background Jobs

APScheduler checks reminders every hour and sends email notifications for upcoming races.

### `data_parser.py` — Prompt Formatter

Converts raw Ergast API race data into formatted text for AI prompts.

### `prediction_service.py` — Championship Prediction Engine

Generates AI-powered championship predictions for the current season:

| Method | Purpose |
|--------|---------|
| `predict_driver_champion()` | Predict driver championship winner with confidence |
| `predict_constructor_champion()` | Predict constructor championship winner with confidence |
| `_calculate_driver_form()` | Analyze ALL completed races this season for a driver |
| `_calculate_constructor_form()` | Analyze ALL completed races this season for a constructor |
| `_predict_driver_points()` | Statistical projection based on current points pace |
| `_predict_constructor_points()` | Statistical projection based on current points pace |
| `_get_ai_prediction()` | AI synthesis combining stats + form + standings |

**Prediction flow:**
1. Fetch current standings and season schedule
2. Calculate form for top 5 drivers/constructors (all completed races)
3. Generate statistical prediction based on points pace
4. AI synthesizes standings + form + remaining races → final prediction
5. Result cached for 6 hours

**Response structure:**
```json
{
  "season": 2026,
  "type": "drivers",
  "races_completed": 12,
  "races_remaining": 12,
  "predicted_champion": {
    "driver_id": "max_verstappen",
    "name": "Max Verstappen",
    "current_points": 250,
    "predicted_final_points": 480,
    "confidence": 0.85
  },
  "top_contenders": [
    {"id": "max_verstappen", "name": "Max Verstappen", "predicted_points": 480, "chance_pct": 0.85},
    {"id": "lewis_hamilton", "name": "Lewis Hamilton", "predicted_points": 390, "chance_pct": 0.12},
    {"id": "lando_norris", "name": "Lando Norris", "predicted_points": 350, "chance_pct": 0.03}
  ],
  "form_analysis": {
    "max_verstappen": {
      "races_analyzed": 12,
      "avg_points": 20.8,
      "total_points": 250,
      "wins": 7,
      "podiums": 10,
      "dnfs": 1,
      "win_pct": 58.3,
      "podium_pct": 83.3,
      "dnf_pct": 8.3
    }
  },
  "ai_reasoning": "Based on current form and the points gap to second place..."
}
```

---

## 8. Database

### PostgreSQL Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| **users** | id, email, password_hash, display_name, created_at, last_login | User accounts |
| **user_favorites** | id, user_id, driver_id, constructor_id, created_at | Favorite drivers |
| **reminders** | id, user_id, race_round, race_year, notify_before_hours, enabled, method, created_at | Race reminders |
| **race_cache** | year, round (composite PK), race_name, circuit, date, results_json, ai_summary_json, cached_at | Legacy race cache |
| **ai_cache** | id, cache_key (unique), response_json, created_at, expires_at | Generic AI response cache |
| **chat_sessions** | id, user_id, title, created_at, updated_at | Chat conversation sessions |
| **chat_messages** | id, session_id, role, content, created_at | Individual chat messages |

### Relationships

```
User ──┬── has many ──→ UserFavorite (cascade delete)
       ├── has many ──→ Reminder (cascade delete)
       └── has many ──→ ChatSession (cascade delete)
                         └── has many ──→ ChatMessage (cascade delete)
```

---

## 9. Frontend — React

### Build System

- **Vite** — Fast dev server, HMR, production bundling
- **TypeScript** — Full type safety
- **Tailwind CSS v4** — Utility-first styling, dark theme
- **react-markdown + remark-gfm** — Markdown rendering in chat
- **react-router-dom** — Client-side routing

### Development

```bash
cd frontend
npm install
npm run dev          # Dev server at :5173 with API proxy
npm run build        # Production build → ../static/dist/
```

### Production

Built into `static/dist/`, served by FastAPI's `StaticFiles`.

---

## 10. Frontend — Components

### Pages

| Component | Route | Description |
|-----------|-------|-------------|
| **HomePage** | `/` | Dashboard with tabs |
| **LoginPage** | `/login` | Email/password login |
| **RegisterPage** | `/register` | New user registration |
| **AccountPage** | `/account` | Profile + Favorites + Reminders |
| **DriverPage** | `/driver/:driverId` | Driver profile + season results |
| **CircuitPage** | `/circuit/:circuitId` | Circuit info + recent races |

### Tabs (Dashboard)

| Tab | Component | Description |
|-----|-----------|-------------|
| Latest Race | `LatestRaceTab` | Podium cards 🥇🥈🥉 + AI summary button |
| Browse Seasons | `BrowseSeasonsTab` | Year input → race list → inline expand |
| Standings | `StandingsTab` | Driver/Constructor tables |
| Reminders | `RemindersTab` | Upcoming races + add reminders |
| 📖 Retrospective | `RetrospectiveTab` | Year selector → AI season narrative |
| ⚔️ Compare | `CompareTab` | Driver H2H: career stats + race-by-race table |
| 🔮 Predictions | `PredictionsTab` | Championship predictions with form analysis |
| 🤖 AI Assistant | `ChatTab` | Free-form F1 chat with history |

### Key Components

| Component | Purpose |
|-----------|---------|
| **Layout** | Header (nav + auth), footer, dark theme wrapper |
| **AuthContext** | JWT storage, login/logout, user state |
| **api.ts** | Fetch wrapper with auth interceptor |

---

## 11. Frontend — State Management

### Authentication (`AuthContext.tsx`)

```
AuthProvider
  ├── user: User | null
  ├── token: string | null (localStorage)
  ├── isAuthenticated: boolean
  ├── isLoading: boolean
  ├── login(email, password) → fetches JWT, loads user
  ├── register(email, password, name) → creates account, logs in
  └── logout() → clears localStorage
```

### Chat State

| State | Type | Purpose |
|-------|------|---------|
| `sessions` | `ChatSession[]` | Sidebar list |
| `activeSession` | `number \| null` | Currently open session |
| `messages` | `ChatMessage[]` | Messages in active session |
| `pendingSessions` | `Set<number>` | Sessions waiting for AI response (persisted to localStorage) |
| `isSessionTyping` | `boolean` | Derived: is current session waiting for AI? |
| `input` | `string` | Current message input |

### Podium Display

Race results show **real podium layout**:
- 🥈 2nd place → **left**
- 🥇 1st place → **center** (bigger, raised)
- 🥉 3rd place → **right**

---

## 12. AI System

### Race Summaries (JSON mode)

1. Fetch race data from Ergast
2. Format via `data_parser.py`
3. Send to Qwen with system prompt (JSON format required)
4. Parse response → `{summary, highlights, insights, answer}`
5. Cache for 24 hours

### Chat (Free-form)

1. User sends message
2. Backend saves message to DB
3. AI processes with F1 system prompt + verified data
4. Fact-checker validates response against real data
5. Response saved to DB
6. Frontend polls every 2s to detect AI response
7. Updates UI when response arrives

### Retrospective

1. Fetch season data (schedule + standings) in parallel
2. Build comprehensive context
3. AI generates season narrative
4. Cache for 12 hours

### Prompt Injection Protection

- Input sanitization (control chars stripped, 2000 char limit)
- HTML escaping before sending to AI
- Pattern blocking: "ignore previous instructions", "you are now", etc.
- Fact-checker validates all statistics

---

## 13. Caching System

### Two-Layer Cache

| Layer | Type | TTL | Purpose |
|-------|------|-----|---------|
| **AICache** | Database | 6-24h | AI-generated responses |
| **RaceCache** | Database | Unlimited | Legacy race data cache |

### Cache Keys

| Pattern | Example | TTL |
|---------|---------|-----|
| `race_{year}_{round}_{query}` | `race_2024_1_` | 24 hours |
| `retro_{year}` | `retro_2024` | 12 hours |

### Flow

```
Request → Check cache → HIT: return cached → DONE
                          ↓
                        MISS: call AI → save to cache → return
```

---

## 13b. Championship Predictions

### Overview

The Championship Prediction feature provides AI-powered predictions for both the Driver and Constructor championships for the **current season only**. Predictions are based on:

1. **Current championship standings** — Real points from the Jolpica-F1 API
2. **Season form analysis** — ALL completed races this season (not just recent ones)
3. **Statistical projection** — Points pace extrapolated to season end
4. **AI synthesis** — Qwen LLM combines all data into a reasoned prediction

### How Predictions Work

#### Step 1: Data Collection

```
predict_driver_champion()
  ├── get_driver_standings(current_year)     → Current championship table
  ├── get_season_schedule(current_year)       → All races + dates
  └── For each of top 5 drivers:
        └── get_driver_season_results()       → Season race-by-race results
```

#### Step 2: Form Analysis

For each of the top 5 drivers/constructors, the service calculates comprehensive form metrics using **ALL completed races** in the current season:

**Driver Form:**
| Metric | Calculation |
|--------|-------------|
| `races_analyzed` | Count of all classified races this season |
| `avg_points` | Total points ÷ races analyzed |
| `total_points` | Sum of points from all races |
| `wins` | Count of P1 finishes |
| `podiums` | Count of P1, P2, P3 finishes |
| `dnfs` | Count of retired/DNF results |
| `win_pct` | (wins ÷ races_analyzed) × 100 |
| `podium_pct` | (podiums ÷ races_analyzed) × 100 |
| `dnf_pct` | (dnfs ÷ races_analyzed) × 100 |

**Constructor Form:**
| Metric | Calculation |
|--------|-------------|
| `races_analyzed` | Count of all races this season |
| `avg_points_per_race` | Total points ÷ races (both drivers combined) |
| `total_points_recent` | Sum of all constructor points |

#### Step 3: Statistical Projection

A simple but effective linear projection based on current points pace:

```python
pace_per_race = current_points / races_completed
predicted_additional = pace_per_race * races_remaining
predicted_final = current_points + predicted_additional
```

This gives a baseline prediction that the AI can adjust based on form, momentum, and DNF risk.

#### Step 4: AI Synthesis

The prediction data is sent to Qwen with a structured prompt:

```
Formula 1 drivers Championship Prediction — Season 2026

CURRENT STANDINGS (Top 5):
  [{"position": 1, "driver_name": "...", "points": 250}, ...]

FORM ANALYSIS (Last 5 Races):
  {"max_verstappen": {"avg_points": 20.8, "wins": 7, ...}, ...}

STATISTICAL PREDICTION (Based on points pace):
  {"max_verstappen": {"predicted_final": 480, ...}, ...}

RACES COMPLETED: 12
RACES REMAINING: 12
```

The AI returns a structured JSON prediction:
```json
{
  "predicted_champion_id": "max_verstappen",
  "predicted_champion_name": "Max Verstappen",
  "predicted_final_points": 480,
  "confidence": 0.85,
  "reasoning": "Based on current form and the 50-point gap...",
  "top_contenders": [
    {"id": "max_verstappen", "name": "Max Verstappen", "predicted_points": 480, "chance_pct": 0.85},
    {"id": "lewis_hamilton", "name": "Lewis Hamilton", "predicted_points": 390, "chance_pct": 0.12}
  ]
}
```

#### Step 5: Merge & Cache

The backend merges statistical and AI predictions, then caches the result for **6 hours** using the `AICache` table. Cache keys:
- `prediction_drivers`
- `prediction_constructors`

### Frontend: PredictionsTab Component

Located at `frontend/src/components/tabs/PredictionsTab.tsx`.

**Design:**
- Two buttons at the top: **🏎️ Drivers Championship** and **🏢 Constructors Championship**
- Both buttons start **gray** (inactive) — click either to load prediction
- Active button turns **red** while loading and after prediction loads
- Prediction auto-loads on button click (no separate "Predict" button)

**UI Sections (when loaded):**

1. **Season Info Bar** — Shows current season year and races completed/total
2. **Predicted Champion Card** — Large card with:
   - 🏆 Trophy icon + champion name
   - Confidence percentage (large, yellow)
   - Current points vs. predicted final points
   - Confidence progress bar (gradient yellow)
3. **Top Contenders Table** — Ranked table with:
   - Medal icons (🥇🥈🥉) for top 3
   - Clickable names linking to driver/constructor pages
   - Predicted final points
   - Championship chance percentage (if AI provided)
4. **AI Analysis** — Free-form text explanation of the prediction
5. **Form Analysis Grid** — Responsive grid (1-3 columns) showing:
   - Driver/constructor name (clickable link)
   - All form metrics (avg points, wins, podiums, win%, DNF%, etc.)
   - Styled cards with borders and stat rows

### API Endpoints

#### GET /api/predictions/drivers

Returns the AI prediction for the current season's driver championship.

**Query Parameters:** None (current year only)

**Response:** `PredictionResponse` JSON object

**Caching:** 6 hours via `AICache`

**Example:**
```bash
curl http://localhost:8000/api/predictions/drivers
```

#### GET /api/predictions/constructors

Returns the AI prediction for the current season's constructor championship.

**Query Parameters:** None (current year only)

**Response:** `PredictionResponse` JSON object

**Caching:** 6 hours via `AICache`

### TypeScript Types

```typescript
interface PredictionResponse {
  season: number;
  type: 'drivers' | 'constructors';
  races_completed: number;
  races_remaining: number;
  predicted_champion: DriverPredictionChampion | ConstructorPredictionChampion | null;
  top_contenders: PredictionContender[];
  form_analysis: Record<string, DriverFormAnalysis | ConstructorFormAnalysis>;
  ai_reasoning: string;
  error?: string;
}

interface DriverPredictionChampion {
  driver_id: string;
  name: string;
  current_points: number;
  predicted_final_points: number;
  confidence: number;
}

interface PredictionContender {
  id: string;
  name: string;
  predicted_points: number;
  chance_pct?: number;
}

interface DriverFormAnalysis {
  races_analyzed: number;
  avg_points: number;
  total_points: number;
  wins: number;
  podiums: number;
  dnfs: number;
  win_pct: number;
  podium_pct: number;
  dnf_pct: number;
}
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Current year only | Predictions only make sense for the active season |
| All completed races | Full season form is more accurate than just last 5 |
| 6-hour cache TTL | Data only changes between races, not during the week |
| No auth required | Predictions are public data, like standings |
| Statistical + AI hybrid | AI alone might hallucinate; stats ground the prediction |
| Graceful AI fallback | If AI unavailable, statistical prediction still works |

### Testing

11 unit tests in `tests/test_predictions.py`:

| Test | Purpose |
|------|---------|
| `test_predict_driver_championship_returns_prediction` | Driver endpoint returns full response |
| `test_predict_driver_champion_structure` | Champion object has required fields |
| `test_predict_constructor_championship_returns_prediction` | Constructor endpoint returns full response |
| `test_predict_constructor_champion_structure` | Champion object has required fields |
| `test_predict_driver_no_year_parameter` | No year param required (current year only) |
| `test_predict_constructor_no_year_parameter` | No year param required (current year only) |
| `test_prediction_works_without_ai` | Statistical fallback when AI unavailable |
| `test_form_analysis_included_in_prediction` | Form analysis present in response |
| `test_races_completed_and_remaining` | Race counts are valid integers ≥ 0 |

All tests use mocked `ErgastClient`, `AISummarizer`, and cache services for deterministic results.

---

## 14. Security

### Authentication

- **JWT tokens** stored in `localStorage`
- **bcrypt** password hashing (work factor 12)
- **Token expiry** handled by JWT claims
- All sensitive routes require `Bearer` token

### Chat Security

| Protection | Implementation |
|-----------|---------------|
| **Input sanitization** | Control chars stripped, 2000 char limit |
| **Rate limiting** | 10 messages per 60s per user (in-memory) |
| **Session max** | 500 messages per session |
| **SQL injection** | SQLAlchemy parameterized queries |
| **Prompt injection** | Pattern blocking + HTML escaping |
| **XSS prevention** | ReactMarkdown element whitelist, no script/iframe |
| **Session ownership** | `WHERE user_id = current_user.id` on every query |

### Rate Limiting

| Protection | Implementation |
|-----------|---------------|
| **Chat** | 10 messages per 60s per user (in-memory) |
| **Ergast API** | Exponential backoff retry (2s, 4s, 8s) on 429 responses |
| **Persistent HTTP client** | Reuses connections to minimize overhead |

### API Security

| Protection | Implementation |
|-----------|---------------|
| **CORS** | `allow_origins=["*"]` (dev — restrict in production) |
| **404 for unknown routes** | Catch-all excludes `/api/*` paths |
| **Error masking** | Internal errors return generic messages |

---

## 15. Docker & Deployment

### docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:18.3-alpine
    ports: 5432:5432
    volumes: postgres_data:/var/lib/postgresql/data
    healthcheck: pg_isready

  f1-assistant:
    build: .
    ports: 8000:8000
    depends_on: postgres (healthy)
    environment: DATABASE_URL, JWT_SECRET, SMTP_*
```

### Dockerfile (Multi-stage)

```
Stage 1: node:20-alpine
  → npm install
  → npm run build
  → Output: /frontend/dist/

Stage 2: python:3.12-slim
  → pip install requirements
  → COPY --from=Stage 1 /frontend/dist → /static/dist/
  → COPY . .
  → CMD uvicorn main:app --host 0.0.0.0 --port 8000
```

### One-Command Deploy

```bash
docker compose up --build
# → http://localhost:8000
```

---

## 16. Testing

### Test Structure

| File | Purpose |
|------|---------|
| `test_api.py` | API endpoint tests (health, races, standings, drivers, circuits) |
| `test_e2e.py` | End-to-end tests against running server |
| `test_retrospective.py` | Season retrospective endpoint tests |
| `test_compare.py` | Driver/constructor comparison tests |
| `test_predictions.py` | Championship prediction tests (service + auth) |
| `test_data_parser.py` | Data parser tests |
| `test_ai_assistant.py` | AI fallback tests |
| `test_push_notifications.py` | Push notification endpoint tests |

### Running Tests

```bash
# Via Docker
docker exec lab9-f1-assistant-1 python -m pytest tests/ -v

# Unit tests only
docker exec lab9-f1-assistant-1 python -m pytest tests/ -k "not e2e" -v
```

### Mocking

- `mock_ai_summarizer` → Returns predictable JSON without Qwen
- `mock_ergast_client` → Returns sample data without network
- `test_app` fixture → TestClient with mocked services

---

## 17. API Reference

### Request/Response Examples

#### GET /api/races/latest

```json
{
  "race_name": "Japanese Grand Prix",
  "circuit": "Suzuka Circuit",
  "date": "2026-03-29",
  "season": "2026",
  "round": 3,
  "ai_response": {
    "summary": "...",
    "highlights": "Winner: ...",
    "insights": "...",
    "answer": ""
  }
}
```

#### GET /api/seasons/2024/retrospective (auth required)

```json
{
  "year": 2024,
  "total_races": 24,
  "races_completed": 24,
  "is_ongoing": false,
  "champion": { "driver_name": "Max Verstappen", "constructor": "Red Bull", "points": 575.0 },
  "constructors_champion": { "constructor": "Red Bull", "points": 860.0 },
  "retrospective": "The 2024 season was defined by..."
}
```

#### GET /api/compare/drivers?a=hamilton&b=max_verstappen

```json
{
  "driver_a": {
    "info": { "driver_id": "hamilton", "full_name": "Lewis Hamilton", "nationality": "British", ... },
    "career": {
      "races": 383, "wins": 105, "podiums": 203, "poles": 104,
      "points": 4990.5, "championships": 7,
      "best_finish": 1, "worst_finish": 24, "dnfs": 0,
      "seasons_competed": [2007, 2008, ..., 2026]
    }
  },
  "driver_b": { ... },
  "head_to_head": {
    "shared_seasons": [2015, 2016, ..., 2026],
    "shared_races": 235,
    "driver_a_wins": 131,
    "driver_b_wins": 104,
    "draws": 0,
    "race_details": [
      {
        "season": 2015, "round": 1, "race_name": "Australian GP",
        "driver_a": { "position": "1", "points": 25.0, "status": "Finished" },
        "driver_b": { "position": "DNF", "points": 0.0, "status": "Engine" },
        "winner": "a"
      }
    ]
  }
}
```

**How it works:**
1. Fetches ALL career results for both drivers (paginated, ~4 API calls per driver)
2. Computes career stats (races, wins, podiums, poles, points, championships)
3. Matches races by `(season, round)` to compute H2H record
4. Classified finish beats unclassified; lower position number wins; same = draw

#### POST /api/chat/sessions/{id}/messages (auth required)

```json
{ "content": "Who won the 2024 Monaco GP?", "save_only": true }
```

Response:
```json
{
  "message": {
    "id": 42,
    "role": "user",
    "content": "Who won the 2024 Monaco GP?",
    "created_at": "2026-04-06T12:00:00"
  }
}
```

---

## 18. Development Guide

### Local Development

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Start backend
pip install -r requirements.txt
uvicorn main:app --reload

# 3. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173 (proxies API to :8000)
```

### Adding a New Endpoint

1. Create `endpoints/new_feature.py`
2. Define router with `APIRouter(prefix="/api/...", tags=["..."])`
3. Add routes with `@router.get()`, `@router.post()`, etc.
4. Import and register in `main.py`:
   ```python
   from endpoints.new_feature import router as new_feature_router
   app.include_router(new_feature_router)
   ```
5. Add TypeScript types to `frontend/src/types/api.ts`
6. Add API wrapper to `frontend/src/services/api.ts`
7. Write tests in `tests/test_new_feature.py`

### Database Migrations

For production, use Alembic. For development:
```python
# Add model to db/models.py
# Tables are auto-created on startup via init_db()
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://f1user:f1password@localhost:5432/f1assistant` | PostgreSQL connection |
| `JWT_SECRET` | `dev-secret-change-me-in-production` | JWT signing key |
| `SMTP_HOST` | `""` | Email server for reminders |
| `SMTP_PORT` | `"587"` | Email port |
| `SMTP_USER` | `""` | Email username |
| `SMTP_PASSWORD` | `""` | Email password |
| `SENDER_EMAIL` | `"f1-assistant@example.com"` | From address |

---

*Last updated: April 2026*
