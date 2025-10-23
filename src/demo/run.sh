#!/bin/bash
set -e

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate
pip install --upgrade google-adk==1.16.0
export SSL_CERT_FILE=$(python -m certifi)

# Kill existing processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start server in background with debug logging to file
echo "Starting server with debug logging to app/server.log..."
uvicorn app.main:app --port 8000 --log-level debug > app/server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start with retries
echo "Waiting for server to become ready..."
MAX_RETRIES=12
RETRY_DELAY=2
for i in $(seq 1 $MAX_RETRIES); do
    sleep $RETRY_DELAY
    if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✓ Server health check passed"
        break
    fi

    if [ $i -eq $MAX_RETRIES ]; then
        echo "Error: Server health check failed after $((MAX_RETRIES * RETRY_DELAY)) seconds"
        echo ""
        echo "Last 20 lines from demo/server.log:"
        tail -20 demo/server.log
        echo ""
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    echo "  Attempt $i/$MAX_RETRIES failed, retrying..."
done

echo ""
echo "✓ Server is running successfully!"
echo "  URL: http://localhost:8000"
echo "  PID: $SERVER_PID"
echo "  Logs: app/server.log"
echo ""
echo "To monitor logs in real-time:"
echo "  tail -f app/server.log"
echo ""
echo "Press CTRL+C to stop the server"

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    echo "Server stopped"
}
trap cleanup EXIT

# Wait for interrupt
wait $SERVER_PID
