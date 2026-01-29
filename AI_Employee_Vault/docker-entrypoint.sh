#!/bin/bash
# AI Employee - Docker Entrypoint
# Starts all services

set -e

echo "========================================"
echo "  AI Employee - Starting Services"
echo "========================================"

# Function to handle shutdown
cleanup() {
    echo "Shutting down AI Employee..."
    kill $DASHBOARD_PID $SCHEDULER_PID 2>/dev/null
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start dashboard
echo "Starting Dashboard..."
cd /app/dashboard
npm start &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 5

# Start scheduler
echo "Starting Scheduler..."
cd /app
python scheduler.py --daemon &
SCHEDULER_PID=$!

echo ""
echo "========================================"
echo "  AI Employee is running!"
echo "========================================"
echo "  Dashboard: http://localhost:3001"
echo "  Scheduler: Running in background"
echo "========================================"
echo ""

# Keep container running
wait
