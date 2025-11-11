#!/bin/bash
# Start WATCHKEEPER Celery Workers and Beat Scheduler

echo "=== Starting WATCHKEEPER Background Workers ==="

# Change to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A src.core.celery_app worker --loglevel=info --concurrency=4 &
WORKER_PID=$!

# Start Celery beat scheduler in background
echo "Starting Celery beat scheduler..."
celery -A src.core.celery_app beat --loglevel=info &
BEAT_PID=$!

echo "Workers started successfully!"
echo "Worker PID: $WORKER_PID"
echo "Beat PID: $BEAT_PID"
echo ""
echo "To stop workers, run:"
echo "  kill $WORKER_PID $BEAT_PID"

# Keep script running
wait
