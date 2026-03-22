#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "Starting backend..."
"$DIR/.venv/bin/python" "$DIR/run_server.py" &
BACKEND_PID=$!

echo "Starting frontend..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

wait
