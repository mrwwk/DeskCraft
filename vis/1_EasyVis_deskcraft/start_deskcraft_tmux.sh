#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUX_SESSION="easyvis_deskcraft"
DEFAULTS_FILE="${DEFAULTS_FILE:-${SCRIPT_DIR}/profiles/kimi_replay_full.json}"
PORT="${PORT:-8093}"

if tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
  echo "Tmux session '${TMUX_SESSION}' already exists."
  echo "Attach to view server: tmux attach -t ${TMUX_SESSION}"
  echo "Open: http://<your-ip>:${PORT}"
  exit 0
fi

tmux new-session -d -s "${TMUX_SESSION}" "cd '${SCRIPT_DIR}' && pip install -q flask 2>/dev/null; python3 app.py --port ${PORT} --host 0.0.0.0 --defaults '${DEFAULTS_FILE}'; echo ''; echo 'Server stopped. Press Enter to close...'; read"

echo "EasyVis DeskCraft started in tmux session: ${TMUX_SESSION}"
echo ""
echo "Open in browser: http://<your-ip>:${PORT}"
echo ""
echo "View server logs:"
echo "  tmux attach -t ${TMUX_SESSION}"
echo ""
echo "Detach without stopping server: Ctrl+b then d"
echo "List sessions: tmux ls"
