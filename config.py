import os

# Ergast API base URL — Jolpica-F1 is the official Ergast replacement
# Ergast (ergast.com) was deprecated end of 2024
ERGAST_BASE_URL = "https://api.jolpi.ca/ergast/f1"

# Default request timeout (seconds)
ERGAST_TIMEOUT = 30.0

# Qwen LLM settings (via local Qwen Code API — OAuth authenticated)
# When running in Docker, use host.docker.internal to reach the host
QWEN_MODEL = os.getenv("QWEN_MODEL", "coder-model")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "http://host.docker.internal:42005/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "my-secret-qwen-key")
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 500

# Fallback when AI is unavailable
USE_AI_FALLBACK = True

# ── Push Notifications (Web Push API) ──
# VAPID keys generated for browser push notifications
VAPID_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg5fo1Mt38inkf3Vw4sYEHyKvm4bAetN_MqPrT5HQ8RhyhRANCAARlfr5UC1dNC4_0g5AUjh42rWO9tlre_FZvLznR_KZP1bEqRRhevH4I_6_oxap0b4LNcs-kML9C7lHNlvXbcSdV"
VAPID_PUBLIC_KEY = "BGV-vlQLV00Lj_SDkBSOHjatY722Wt78Vm8vOdH8pk_VsSpFGF68fgj_r-jFqnRvgs1yz6Qwv0LuUc2W9dtxJ1U="
VAPID_CLAIMS = {"sub": "mailto:f1-assistant@example.com"}
