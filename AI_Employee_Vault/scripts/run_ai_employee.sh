#!/bin/bash
# ===========================================
# AI Employee Startup Script
# ===========================================
# This script starts all the AI Employee components:
# 1. Gmail Watcher
# 2. LinkedIn Watcher
# 3. Approval Workflow Monitor
# 4. Orchestrator
#
# Usage: ./run_ai_employee.sh start|stop|status
# ===========================================

VAULT_PATH="/mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault"
WATCHERS_PATH="$VAULT_PATH/watchers"
SCRIPTS_PATH="$VAULT_PATH/scripts"
LOGS_PATH="$VAULT_PATH/Logs/System"
PID_PATH="$SCRIPTS_PATH/pids"

# Create necessary directories
mkdir -p "$LOGS_PATH"
mkdir -p "$PID_PATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[AI Employee]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

start_component() {
    local name=$1
    local script=$2
    local pid_file="$PID_PATH/${name}.pid"
    local log_file="$LOGS_PATH/${name}_$(date +%Y%m%d).log"

    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        warn "$name is already running (PID: $(cat $pid_file))"
        return 1
    fi

    log "Starting $name..."
    nohup python3 "$script" "$VAULT_PATH" >> "$log_file" 2>&1 &
    echo $! > "$pid_file"
    log "$name started (PID: $!)"
}

stop_component() {
    local name=$1
    local pid_file="$PID_PATH/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping $name (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
            log "$name stopped"
        else
            warn "$name is not running"
            rm "$pid_file"
        fi
    else
        warn "$name pid file not found"
    fi
}

status_component() {
    local name=$1
    local pid_file="$PID_PATH/${name}.pid"

    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name: Running (PID: $(cat $pid_file))"
    else
        echo -e "  ${RED}✗${NC} $name: Stopped"
    fi
}

case "$1" in
    start)
        echo ""
        echo "=========================================="
        echo "   AI Employee - Starting All Services"
        echo "=========================================="
        echo ""

        # Start all components
        start_component "gmail_watcher" "$WATCHERS_PATH/gmail_watcher.py"
        start_component "linkedin_watcher" "$WATCHERS_PATH/linkedin_watcher.py"
        start_component "approval_workflow" "$WATCHERS_PATH/approval_workflow.py"
        start_component "orchestrator" "$WATCHERS_PATH/orchestrator.py"

        echo ""
        log "All services started!"
        log "Logs are in: $LOGS_PATH"
        echo ""
        ;;

    stop)
        echo ""
        echo "=========================================="
        echo "   AI Employee - Stopping All Services"
        echo "=========================================="
        echo ""

        stop_component "orchestrator"
        stop_component "approval_workflow"
        stop_component "linkedin_watcher"
        stop_component "gmail_watcher"

        echo ""
        log "All services stopped"
        echo ""
        ;;

    status)
        echo ""
        echo "=========================================="
        echo "   AI Employee - Service Status"
        echo "=========================================="
        echo ""
        echo "Services:"
        status_component "gmail_watcher"
        status_component "linkedin_watcher"
        status_component "approval_workflow"
        status_component "orchestrator"
        echo ""
        echo "Vault: $VAULT_PATH"
        echo "Logs:  $LOGS_PATH"
        echo ""
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all AI Employee services"
        echo "  stop    - Stop all AI Employee services"
        echo "  status  - Show status of all services"
        echo "  restart - Restart all services"
        exit 1
        ;;
esac

exit 0
