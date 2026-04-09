#!/bin/bash
# Qwen Token Refresh Script
# This script monitors the qwen-code-api token and restarts the container
# to reload credentials before they expire.

set -e

CREDS_FILE="$HOME/.qwen/oauth_creds.json"
CONTAINER_NAME="qwen-code-api-qwen-code-api-1"
REFRESH_BUFFER_MINUTES=10  # Refresh this many minutes before expiry

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_creds() {
    if [ ! -f "$CREDS_FILE" ]; then
        log "ERROR: Credentials file not found at $CREDS_FILE"
        log "Please run '/qwen_auth' in the autochecker bot first."
        exit 1
    fi
}

get_token_expiry() {
    python3 -c "
import json
with open('$CREDS_FILE') as f:
    creds = json.load(f)
print(creds.get('expiry_date', 0))
"
}

get_current_time_ms() {
    python3 -c "import time; print(int(time.time() * 1000))"
}

restart_container() {
    log "Restarting $CONTAINER_NAME to reload credentials..."
    docker restart "$CONTAINER_NAME" 2>/dev/null || {
        log "ERROR: Failed to restart container"
        exit 1
    }
    log "Container restarted successfully"
}

check_health() {
    local health
    health=$(curl -sf http://localhost:42005/health 2>/dev/null)
    if [ -z "$health" ]; then
        log "WARNING: Health check failed"
        return 1
    fi
    
    local status
    status=$(echo "$health" | python3 -c "import sys, json; print(json.load(sys.stdin)['default_account']['status'])" 2>/dev/null)
    
    if [ "$status" = "healthy" ]; then
        return 0
    else
        return 1
    fi
}

# If --once flag is passed, just refresh once and exit
if [ "$1" = "--once" ]; then
    log "Single token refresh requested"
    check_creds
    restart_container
    log "Waiting 5 seconds for container to start..."
    sleep 5
    
    if check_health; then
        log "SUCCESS: Token is healthy"
        exit 0
    else
        log "WARNING: Container restarted but health check failed"
        exit 1
    fi
fi

# Daemon mode: continuously monitor and refresh
log "Starting token monitor daemon (Ctrl+C to stop)"
log "Watching: $CREDS_FILE"
log "Container: $CONTAINER_NAME"
log "Refresh buffer: ${REFRESH_BUFFER_MINUTES} minutes before expiry"
echo ""

while true; do
    check_creds
    
    expiry_ms=$(get_token_expiry)
    current_ms=$(get_current_time_ms)
    buffer_ms=$((REFRESH_BUFFER_MINUTES * 60 * 1000))
    threshold_ms=$((expiry_ms - buffer_ms))
    
    if [ "$current_ms" -ge "$threshold_ms" ]; then
        log "⚠️  Token approaching expiry (within ${REFRESH_BUFFER_MINUTES} min buffer)"
        restart_container
        
        # Wait and verify
        sleep 5
        if check_health; then
            log "✅ Token refreshed successfully"
        else
            log "❌ Token refresh failed - health check unsuccessful"
        fi
        echo ""
    else
        # Calculate minutes remaining
        remaining_ms=$((expiry_ms - current_ms))
        remaining_min=$((remaining_ms / 60000))
        
        if [ "$remaining_min" -lt 60 ]; then
            log "⏰ Token expires in ${remaining_min} minutes - waiting..."
        else
            remaining_hr=$((remaining_min / 60))
            remaining_min=$((remaining_min % 60))
            log "⏰ Token expires in ${remaining_hr}h ${remaining_min}m - waiting..."
        fi
    fi
    
    # Check every 2 minutes
    sleep 120
done
