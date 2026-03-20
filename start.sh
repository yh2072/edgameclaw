#!/bin/bash
# Created by Yuqi Hang (github.com/yh2072)
# EdGameClaw — Quick start script

set -e

cd "$(dirname "$0")"
ROOT_DIR="$(pwd)"

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

BIND_HOST="${BIND_HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo ""
echo "  🐸 EdGameClaw — AI Game-Based Learning Studio"
echo "  ─────────────────────────────────────────────"
echo "  Studio: http://$BIND_HOST:$PORT/"
echo ""

# Kill any existing process on port 3100
if lsof -ti :3100 >/dev/null 2>&1; then
  echo "  Clearing port 3100..."
  lsof -ti :3100 | xargs kill -9 2>/dev/null || true
  sleep 0.5
fi

# Start Node engine state server in background
if [ -d node ]; then
  echo "  Starting Node engine server on port 3100..."
  (cd "$ROOT_DIR/node" && PORT=3100 node server.js) &
  NODE_PID=$!
fi

# Resolve uvicorn: prefer venv, then conda env, then system PATH
if [ -f "$ROOT_DIR/.venv/bin/uvicorn" ]; then
  UVICORN="$ROOT_DIR/.venv/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
  UVICORN="uvicorn"
else
  echo "  ERROR: uvicorn not found. Activate your venv first:"
  echo "    source .venv/bin/activate"
  exit 1
fi

# Start Python server (must run from ROOT_DIR so server.py is importable)
cd "$ROOT_DIR"
"$UVICORN" server:app --host "$BIND_HOST" --port "$PORT"

# Cleanup
if [ -n "$NODE_PID" ]; then
  kill "$NODE_PID" 2>/dev/null || true
fi
