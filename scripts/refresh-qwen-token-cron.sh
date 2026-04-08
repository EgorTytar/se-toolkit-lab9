#!/bin/bash
# Simple token refresh - just restart the container
# Use this in cron: */30 * * * * /opt/f1-assistant/scripts/refresh-qwen-token.sh --once >> /var/log/qwen-token-refresh.log 2>&1

set -e

CONTAINER_NAME="qwen-code-api-qwen-code-api-1"
CREDS_FILE="$HOME/.qwen/.oauth_creds.json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "ERROR: Container $CONTAINER_NAME not found"
    exit 1
fi

# Check if creds file exists
if [ ! -f "$CREDS_FILE" ]; then
    log "WARNING: No credentials file found. Run /qwen_auth in autochecker bot."
    exit 1
fi

# Check if token is expired
EXPIRY_MS=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['expiry_date'])")
CURRENT_MS=$(python3 -c "import time; print(int(time.time() * 1000))")

if [ "$CURRENT_MS" -ge "$EXPIRY_MS" ]; then
    log "Token is EXPIRED. Please run /qwen_auth in autochecker bot."
    exit 1
fi

# Restart container to reload credentials
docker restart "$CONTAINER_NAME"
log "Container restarted"

# Wait and check health
sleep 5
HEALTH=$(curl -sf http://localhost:42005/health || echo "")

if [ -n "$HEALTH" ]; then
    STATUS=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['default_account']['status'])" 2>/dev/null || echo "unknown")
    EXPIRES=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['default_account']['expires_in'])" 2>/dev/null || echo "unknown")
    log "Health: status=$STATUS, expires_in=$EXPIRES"
    
    if [ "$STATUS" = "healthy" ]; then
        log "SUCCESS"
        exit 0
    fi
fi

log "WARNING: Health check inconclusive"
exit 1
