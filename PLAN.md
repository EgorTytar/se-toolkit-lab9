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
| 8. Testing | Comprehensive test suite, all passing |

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
| **Full Test Suite** | Unit tests + e2e tests against running server |

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
✅ All tests pass  
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
| **Free-Form Q&A** | Ask any question about F1 — "Who has the most wins at Monaco?" "How did Hamilton do in 2021?" | High |
| **Driver Head-to-Head** | Compare two drivers side-by-side: wins, podiums, points, head-to-head qualifying/race record | Medium |
| **Team Comparison** | Constructor head-to-head with historical data and season-over-season trends | Medium |
| **Circuit Pages** | Track information, lap records, most wins, recent results, layout diagram | Medium |
| **Championship Prediction** | AI-powered championship outcome prediction based on current form and remaining races | Low |

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
│   ├── qa_engine.py           # Free-form Q&A with context
│   ├── comparison.py          # Driver/team head-to-head
│   ├── prediction.py          # Championship prediction engine
│   └── circuit_data.py        # Circuit information & stats
├── endpoints/
│   ├── auth.py                # POST /api/auth/register, /api/auth/login
│   ├── users.py               # GET/PUT /api/users/me, /api/users/me/favorites
│   ├── reminders.py           # GET/POST /api/reminders
│   ├── retrospective.py       # GET /api/seasons/{year}/retrospective
│   ├── qa.py                  # POST /api/ask
│   ├── compare.py             # GET /api/compare/drivers?a=x&b=y
│   └── predictions.py         # GET /api/predictions/*
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
| GET | `/api/users/me/favorites/` | Get favorite drivers |
| POST | `/api/users/me/favorites/` | Add favorite |
| DELETE | `/api/users/me/favorites/{id}` | Remove favorite |
| GET | `/api/reminders/` | List user's race reminders |
| POST | `/api/reminders/` | Create a reminder |
| PUT | `/api/reminders/{id}` | Update a reminder |
| DELETE | `/api/reminders/{id}` | Delete a reminder |
| GET | `/api/chat/sessions` | List user's chat sessions |
| POST | `/api/chat/sessions` | Create new chat session |
| GET | `/api/chat/sessions/{id}` | Get session with messages |
| DELETE | `/api/chat/sessions/{id}` | Delete session |
| POST | `/api/chat/sessions/{id}/messages` | Save user message |
| POST | `/api/chat/sessions/{id}/generate` | Generate AI response |
| GET | `/api/circuits/{circuit_id}` | Circuit information and stats |
| GET | `/api/seasons/{year}/schedule` | Season race schedule |

### Implementation Order

1. **Database (PostgreSQL)** — ✅ DONE: foundation for all V2 features
2. **Personal Accounts** — ✅ DONE: registration, login (JWT), profiles
3. **Race Reminders** — ✅ DONE: email scheduler, user-configured alerts
4. **AI Assistant Chat** — ✅ DONE: free-form Q&A with verified data + web search
5. **Frontend Migration** — ✅ DONE: React 18 + TypeScript + Tailwind CSS
6. **Season Retrospective** — ✅ DONE: AI season narratives
7. **Driver Head-to-Head** — ✅ DONE: career stats + race-by-race H2H record
8. **Team Comparison** — ✅ DONE: constructor H2H with historical data
9. **Championship Prediction** — ✅ DONE: AI-powered predictions with form analysis

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
| Prompt injection attacks | Medium | Input sanitization, pattern blocking, HTML escaping |
| XSS in chat messages | Medium | Markdown element whitelist, script/iframe blocking |
| Chat API abuse | Medium | Rate limiting (10 msg/min), session max (500 msgs) |

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
1. Latest Race tab → see podium cards + race results
2. Click 🤖 Get AI Summary → generates detailed analysis (requires login)
3. Browse Seasons → enter 2024 → click any race → inline AI summary
4. Standings → 2024 → Drivers table → click a driver name → driver page
5. Reminders tab → see upcoming races → add reminder
6. 🔮 Predictions → click Drivers/Constructors → AI championship prediction with form analysis
7. 🤖 AI Assistant tab → ask any F1 question → get verified answer
8. Show error handling → enter year 1940 or 2099 → friendly message
9. Account tab → profile, favorites, reminders management
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

---

## Production Deployment to VM

### Prerequisites

- Ubuntu 22.04+ VM with Docker and Docker Compose installed
- Domain name (e.g. `f1.example.com`) pointing to VM IP
- SSL certificate (Let's Encrypt via Caddy or Nginx)
- SMTP credentials for email reminders (optional)
- Qwen AI endpoint accessible from VM

### Step 1: Prepare the VM

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose (usually included with Docker)
docker compose version

# Create app directory
mkdir -p /opt/f1-assistant
cd /opt/f1-assistant
```

### Step 2: Deploy Application

```bash
# Clone or copy project files to VM
scp -r . user@vm-ip:/opt/f1-assistant/

# Copy .env with production values
cp .env.example .env
nano .env
```

### Step 3: Configure Environment (`.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://f1user:STRONG_PASSWORD@postgres:5432/f1_assistant
JWT_SECRET=generate-a-long-random-string-here

# AI (Qwen)
QWEN_API_KEY=your-api-key
QWEN_BASE_URL=http://host.docker.internal:42005/v1
QWEN_MODEL=coder-model

# SMTP (for email reminders — optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@f1-assistant.com

# VAPID (for push notifications)
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_CLAIMS=mailto:admin@f1-assistant.com
```

Generate secrets:
```bash
# JWT Secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# VAPID Keys
python3 -c "
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
import base64
key = ec.generate_private_key(ec.SECP256R1(), default_backend())
priv = base64.urlsafe_b64encode(key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())).decode()
pub = base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)).decode()
print(f'VAPID_PRIVATE_KEY={priv}')
print(f'VAPID_PUBLIC_KEY={pub}')
"
```

### Step 4: Start Services

```bash
cd /opt/f1-assistant
docker compose up -d --build

# Check logs
docker compose logs -f f1-assistant

# Verify health
curl http://localhost:8000/health
```

### Step 5: Add Reverse Proxy with SSL

**Option A: Caddy (automatic HTTPS)**

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

# Configure Caddy
sudo nano /etc/caddy/Caddyfile
```

`/etc/caddy/Caddyfile`:
```
f1.example.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl restart caddy
```

**Option B: Nginx + Certbot**

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/f1-assistant
```

`/etc/nginx/sites-available/f1-assistant`:
```nginx
server {
    listen 80;
    server_name f1.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/f1-assistant /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d f1.example.com
```

### Step 6: Production Hardening

**1. Restrict CORS**

In `config.py` or `main.py`, change:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://f1.example.com"],  # Not ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**2. Use production database password**

Ensure `DATABASE_URL` uses a strong password (not the default).

**3. Set up database backups**

```bash
# Backup script
#!/bin/bash
docker exec lab9-postgres-1 pg_dump -U f1user f1_assistant > /backups/f1_$(date +%Y%m%d).sql

# Cron: daily at 3am
0 3 * * * /opt/f1-assistant/backup.sh
```

**4. Enable auto-restart on failure**

`docker-compose.yml`:
```yaml
services:
  f1-assistant:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
```

**5. Set up monitoring**

```bash
# Simple health check cron
*/5 * * * * curl -sf http://localhost:8000/health || echo "F1 Assistant down" | mail -s "Alert" admin@example.com
```

### Step 7: Verify Deployment

```bash
# 1. Health check
curl https://f1.example.com/health

# 2. Test race endpoint
curl https://f1.example.com/api/races/latest

# 3. Test standings
curl https://f1.example.com/api/standings/drivers?year=2025

# 4. Test predictions
curl https://f1.example.com/api/predictions/drivers

# 5. Open browser and test full UI
# https://f1.example.com
```

### Rollback Plan

```bash
# If something breaks, rollback to previous image
docker compose down
docker compose up -d --build  # Rebuilds from current code

# Or restore from backup
docker exec -i lab9-postgres-1 psql -U f1user -d f1_assistant < /backups/f1_20250401.sql
```

### Quick Commands Reference

```bash
# Start/stop
docker compose up -d
docker compose down

# View logs
docker compose logs -f f1-assistant
docker compose logs -f postgres

# Restart service
docker compose restart f1-assistant

# Run tests
docker exec lab9-f1-assistant-1 python -m pytest tests/ -v --ignore=tests/test_e2e.py

# Clear AI cache
docker exec lab9-f1-assistant-1 python3 -c "
import asyncio
from sqlalchemy import delete
from db.database import async_session
from db.models import AICache
async def clear():
    async with async_session() as db:
        await db.execute(delete(AICache))
        await db.commit()
asyncio.run(clear())
"

# Database access
docker exec -it lab9-postgres-1 psql -U f1user -d f1_assistant

# Update deployment
git pull
docker compose up -d --build
```

---

## Project Status: ✅ COMPLETE — Ready for Deployment

All planned features implemented, tested, and documented. No pending development tasks.

### Feature Checklist

| Feature | Status |
|---------|--------|
| Latest Race AI Summaries | ✅ |
| Season Browsing | ✅ |
| Driver Standings | ✅ |
| Constructor Standings | ✅ |
| Driver Pages | ✅ |
| Circuit Pages | ✅ |
| User Accounts + JWT Auth | ✅ |
| Favorites System | ✅ |
| Race Reminders (Email) | ✅ |
| AI Chat Assistant | ✅ |
| Season Retrospective | ✅ |
| Driver Head-to-Head | ✅ |
| Constructor Comparison | ✅ |
| Constructor Pages | ✅ |
| Teammate Mode | ✅ |
| Championship Predictions | ✅ |
| Browser Push Notifications | ✅ |
| Reminder Editing | ✅ |
| AI Response Caching | ✅ |
| Docker Deployment | ✅ |
| Test Suite | ✅ |
| Documentation | ✅ |

### Remaining Features

All core features are implemented and shipped. Future enhancements could include:

| Feature | Notes |
|---------|-------|
| Live Race Weekend Enhancements | Push notifications for session start, real-time timing screen |
| Push Notification Settings | User-level preferences for notification types and quiet hours |
| Historical Predictions | Predictions for past seasons for retrospective analysis |
```
