# Ergast API base URL — Jolpica-F1 is the official Ergast replacement
# Ergast (ergast.com) was deprecated end of 2024
ERGAST_BASE_URL = "https://api.jolpi.ca/ergast/f1"

# Default request timeout (seconds)
ERGAST_TIMEOUT = 10.0

# Qwen LLM settings (via local Qwen Code API — OAuth authenticated)
# When running in Docker, use host.docker.internal to reach the host
QWEN_MODEL = "coder-model"
QWEN_BASE_URL = "http://host.docker.internal:42005/v1"
QWEN_API_KEY = "my-secret-qwen-key"
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 500

# Fallback when AI is unavailable
USE_AI_FALLBACK = True
