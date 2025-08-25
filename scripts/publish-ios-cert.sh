#!/usr/bin/env bash
# iOS Certificate Publishing Helper
# Serves certificates with correct MIME types for iOS installation

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_SERVER="$REPO_ROOT/cert_server.py"
PID_FILE="/tmp/ghost-writer-cert-server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to start the server
start_server() {
    if is_running; then
        echo -e "${YELLOW}Certificate server is already running (PID: $(cat $PID_FILE))${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Starting certificate server...${NC}"
    
    # Activate virtual environment if it exists
    if [ -d "$REPO_ROOT/.venv" ]; then
        source "$REPO_ROOT/.venv/bin/activate"
    fi
    
    # Start server in background
    nohup python3 "$CERT_SERVER" > /tmp/ghost-writer-cert-server.log 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✅ Certificate server started successfully${NC}"
        echo ""
        echo "📱 iOS Installation URLs:"
        echo "  Profile:     https://100.111.114.84:8443/ssl-certs/ed-dev-root.mobileconfig"
        echo "  Certificate: https://100.111.114.84:8443/ssl-certs/ca-certificate.der"
        echo "  Web UI:      https://100.111.114.84:8443/"
        echo ""
        echo "View logs: tail -f /tmp/ghost-writer-cert-server.log"
    else
        echo -e "${RED}❌ Failed to start certificate server${NC}"
        [ -f /tmp/ghost-writer-cert-server.log ] && tail -20 /tmp/ghost-writer-cert-server.log
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if ! is_running; then
        echo -e "${YELLOW}Certificate server is not running${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping certificate server (PID: $PID)...${NC}"
    kill "$PID"
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ Certificate server stopped${NC}"
}

# Function to check server status
check_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Certificate server is running (PID: $PID)${NC}"
        echo ""
        echo "📱 Access URLs:"
        echo "  https://100.111.114.84:8443/ssl-certs/ed-dev-root.mobileconfig"
        echo "  https://100.111.114.84:8443/ssl-certs/ca-certificate.der"
    else
        echo -e "${RED}❌ Certificate server is not running${NC}"
        echo ""
        echo "Start with: $0 start"
    fi
}

# Function to test MIME types
test_mime() {
    echo "Testing MIME types..."
    echo ""
    
    echo "1. Testing .mobileconfig:"
    curl -k -I https://localhost:8443/ssl-certs/ed-dev-root.mobileconfig 2>/dev/null | grep -i content-type || echo "  Failed to connect"
    
    echo ""
    echo "2. Testing .der:"
    curl -k -I https://localhost:8443/ssl-certs/ca-certificate.der 2>/dev/null | grep -i content-type || echo "  Failed to connect"
}

# Main command handling
case "${1:-status}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        check_status
        ;;
    test)
        test_mime
        ;;
    *)
        echo "Ghost Writer iOS Certificate Server"
        echo "Usage: $0 {start|stop|restart|status|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the certificate server"
        echo "  stop     - Stop the certificate server"
        echo "  restart  - Restart the certificate server"
        echo "  status   - Check server status"
        echo "  test     - Test MIME type configuration"
        exit 1
        ;;
esac