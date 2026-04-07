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

# ── Push Notifications (Web Push API) ──
# Generate VAPID keys with: python -c "from pywebpush import webpush; print(webpush.generate_vapid_keys())"
# Or run: openssl ecparam -genkey -name prime256v1 | openssl ec -text -noout (then convert)
# Quick way: python -c "from cryptography.hazmat.primitives.asymmetric import ec; from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption; import base64; key=ec.generate_private_key(ec.SECP256R1(), default_backend()); print('Private:', base64.urlsafe_b64encode(key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())).decode()); print('Public:', base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.SubjectPublicKeyInfo, PublicFormat.SubjectPublicKeyInfo)).decode())"
VAPID_PRIVATE_KEY = "your-vapid-private-key-here"
VAPID_PUBLIC_KEY = "your-vapid-public-key-here"
VAPID_CLAIMS = {"sub": "mailto:f1-assistant@example.com"}
