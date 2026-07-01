#!/bin/bash
# EasyVis - Quick Start Script
# Usage: bash run.sh [--port 8080] [--llm-url URL] [--llm-model MODEL]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
PORT=8080
LLM_URL=""
LLM_MODEL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port|-p) PORT="$2"; shift 2;;
    --llm-url) LLM_URL="$2"; shift 2;;
    --llm-model) LLM_MODEL="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

# Install dependencies if needed
pip install -q flask 2>/dev/null

echo "Starting EasyVis on port $PORT..."
echo "Open http://<your-ip>:$PORT in browser"
echo ""

# Build command
CMD="python3 app.py --port $PORT"
[ -n "$LLM_URL" ] && CMD="$CMD --llm-url $LLM_URL"
[ -n "$LLM_MODEL" ] && CMD="$CMD --llm-model $LLM_MODEL"

cd "$SCRIPT_DIR"
exec $CMD
