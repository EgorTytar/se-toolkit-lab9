# F1 Race Assistant

AI-powered Formula 1 dashboard with real-time race data, standings, predictions, and a smart chat assistant.

## Demo

### Screenshots

**Dashboard — Latest Race**
![Dashboard](docs/screenshots/dashboard.png)

**Championship Predictions**
![Predictions](docs/screenshots/predictions.png)

**Driver Comparison**
![Comparison](docs/screenshots/compare.png)

**AI Chat Assistant**
![Chat](docs/screenshots/chat.png)

### Product Context

**End Users:** Formula 1 fans who want quick, engaging race recaps and championship analysis without browsing multiple websites or watching full race replays.

**Problem:** F1 fans must visit multiple websites (official F1 site, news outlets, stats pages) to get race results, standings, and analysis. AI-generated content is scattered across social media and not personalized. There is no single dashboard that combines real race data with AI-powered insights, predictions, and conversation.

**Our Solution:** A single web application that pulls real race data from the Jolpica-F1 API and uses AI to generate race summaries, season analysis, championship predictions, and free-form Q&A — all in one place with a modern dark-themed UI.

## Features

### Implemented

| Feature | Description |
|---------|-------------|
| Latest Race AI Summaries | Podium cards 🥇🥈🥉 + AI-generated race summaries with highlights and insights |
| Season Browsing | Explore any F1 season (1950–present) with full race calendar and inline AI summaries |
| Driver Standings | Championship table for any year, clickable driver names |
| Constructor Standings | Team championship table for any year, clickable team names |
| Driver Pages | Full profile with season-by-season race results |
| Circuit Pages | Track info with recent race history |
| User Accounts + JWT Auth | Registration, login, profiles with password hashing (bcrypt) |
| Favorites System | Save favorite drivers and teams (heart button) |
| Race Reminders | Email notifications before upcoming races with APScheduler |
| AI Chat Assistant | Free-form F1 Q&A with verified data, web search fallback, conversation history |
| Driver Head-to-Head | Career stats comparison + race-by-race H2H record |
| Constructor Comparison | Team-vs-team comparison with historical data |
| Constructor Pages | Team profile with year selector and season results for both drivers |
| Teammate Mode | Filter H2H to only races where drivers shared a team |
| Championship Predictions | AI-powered predictions with form analysis, confidence levels, and contender odds (current season) |
| Browser Push Notifications | Web Push API with VAPID keys, service worker, scheduler integration |
| Reminder Editing | Edit reminder time and notification method (email/push/all) |
| AI Response Caching | 6-24 hour TTL depending on content type |
| Test Suite | 64 unit tests passing |

## Usage

### 1. Start the Application

```bash
# One command — builds and starts everything
docker compose up --build
```

Open **`http://localhost:8000`** in your browser.

### 2. Explore the Dashboard

No account needed for browsing:
- **Browse Seasons** — Enter any year (1950–present) to see the full race calendar
- **Standings** — Driver and Constructor championship tables
- **Compare** — Head-to-head driver and constructor comparisons
- **Latest Race** — View podium cards and basic race results

### 3. Create an Account

Click **Account → Register** to unlock AI-powered features:
- **AI Race Summaries** — AI-generated race summaries with highlights and insights
- **Predictions** — AI-powered championship predictions with form analysis
- **AI Assistant** — Free-form F1 Q&A with verified data and web search fallback
- Save favorite drivers and teams
- Set email/push reminders for upcoming races
- View season retrospectives

### 4. Run Tests

```bash
docker exec lab9-f1-assistant-1 python -m pytest tests/ -v --ignore=tests/test_e2e.py
```

## Deployment

### Target OS

Ubuntu 24.04 LTS (same as university VMs).

### Prerequisites (What Should Be Installed on the VM)

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose (included with Docker)
docker compose version

# Optional: reverse proxy for HTTPS
# Option A: Caddy
sudo apt install -y caddy

# Option B: Nginx + Certbot
sudo apt install nginx certbot python3-certbot-nginx
```

### Step-by-Step Deployment

**1. Copy project files to VM:**

```bash
scp -r . user@vm-ip:/opt/f1-assistant/
# Or clone from GitHub:
git clone https://github.com/EgorTytar/se-toolkit-hackathon.git /opt/f1-assistant
cd /opt/f1-assistant
```

**2. Configure environment variables:**

```bash
cp .env.example .env
nano .env
```

Edit `.env` with production values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://f1user:STRONG_PASSWORD@postgres:5432/f1_assistant
JWT_SECRET=generate-a-long-random-string

# AI (Qwen via OpenAI-compatible endpoint)
QWEN_API_KEY=your-api-key
QWEN_BASE_URL=http://host.docker.internal:42005/v1
QWEN_MODEL=coder-model

# SMTP (for email reminders — optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# VAPID (for push notifications)
VAPID_PRIVATE_KEY=your-private-key
VAPID_PUBLIC_KEY=your-public-key
VAPID_CLAIMS=mailto:admin@example.com
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

**3. Start services:**

```bash
docker compose up -d --build
```

**4. Verify deployment:**

```bash
# Check health
curl http://localhost:8000/health

# Check logs
docker compose logs -f f1-assistant
```

**5. (Optional) Add HTTPS with Caddy:**

Create `/etc/caddy/Caddyfile`:

```
your-domain.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl restart caddy
```

**6. (Optional) Add HTTPS with Nginx + Certbot:**

```bash
sudo nano /etc/nginx/sites-available/f1-assistant
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

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
sudo certbot --nginx -d your-domain.com
```

### Production Notes

- **CORS:** Change `allow_origins=["*"]` in `main.py` to your domain in production
- **Database backups:** Set up daily `pg_dump` cron job
- **Monitoring:** Add health check cron (`*/5 * * * * curl -sf localhost:8000/health`)
- **Auto-restart:** `docker-compose.yml` has `restart: unless-stopped`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.12 + FastAPI (async) |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **Database** | PostgreSQL 18 (asyncpg + SQLAlchemy) |
| **AI** | Qwen via OpenAI-compatible endpoint |
| **External API** | Jolpica-F1 (Ergast mirror at api.jolpi.ca) |
| **Containerization** | Docker + Docker Compose |
| **Scheduler** | APScheduler (background reminder checks) |
| **Push Notifications** | Web Push API + pywebpush + service worker |

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | React SPA | ❌ |
| GET | `/health` | Health check | ❌ |
| GET | `/api/races/latest` | AI race summary | ✅ |
| GET | `/api/races/latest/results` | Basic race results | ❌ |
| GET | `/api/races/{year}/{round}` | AI summary for specific race | ✅ |
| GET | `/api/races/{year}/{round}/results` | Basic results + circuit info | ❌ |
| GET | `/api/seasons/{year}/schedule` | Season race schedule | ❌ |
| GET | `/api/standings/drivers?year=X` | Driver standings | ❌ |
| GET | `/api/standings/constructors?year=X` | Constructor standings | ❌ |
| GET | `/api/drivers/{driver_id}` | Driver profile + results | ❌ |
| GET | `/api/circuits/{circuit_id}` | Circuit info + recent results | ❌ |
| GET | `/api/compare/drivers?a=X&b=Y` | Driver head-to-head comparison | ❌ |
| GET | `/api/compare/constructors?a=X&b=Y` | Constructor comparison | ❌ |
| GET | `/api/predictions/drivers` | AI driver championship prediction | ✅ |
| GET | `/api/predictions/constructors` | AI constructor championship prediction | ✅ |
| GET | `/api/seasons/{year}/retrospective` | AI season retrospective | ✅ |
| POST | `/api/auth/register` | Register user | ❌ |
| POST | `/api/auth/login` | Login → JWT | ❌ |
| GET | `/api/users/me` | Current user profile | ✅ |
| GET/POST/PUT/DELETE | `/api/reminders` | Race reminders | ✅ |
| GET/POST/DELETE | `/api/chat/sessions` | Chat session management | ✅ |
| POST | `/api/chat/sessions/{id}/generate` | Generate AI chat response | ✅ |

## Security

- **Input sanitization** — Strips control characters, truncates to 2000 chars
- **Rate limiting** — 10 chat messages per 60 seconds per user
- **Prompt injection protection** — Blocks "ignore instructions" patterns
- **SQL injection prevention** — SQLAlchemy parameterized queries
- **Session ownership** — Users can only access their own data
- **Password hashing** — bcrypt with work factor 12

## Data Source

All race data comes from the **Jolpica-F1 API** (`api.jolpi.ca`) — a community-maintained, fully compatible mirror of the legacy Ergast F1 API.
