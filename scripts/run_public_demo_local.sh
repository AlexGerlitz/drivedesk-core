#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"

cd "$ROOT"

if [[ -n "${DRIVEDESK_PYTHON:-}" && -x "$DRIVEDESK_PYTHON" ]]; then
  PYTHON_BIN="$DRIVEDESK_PYTHON"
elif [[ -n "${PUBLIC_EXPORT_PYTHON:-}" && -x "$PUBLIC_EXPORT_PYTHON" ]]; then
  PYTHON_BIN="$PUBLIC_EXPORT_PYTHON"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python is required" >&2
  exit 1
fi

export PYTHONPATH="$ROOT/apps/api:$ROOT/apps/worker:$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"

echo "DriveDesk public demo API"
echo "API: http://$HOST:$PORT"
echo "Health: http://$HOST:$PORT/health"
echo "Demo payload: http://$HOST:$PORT/demo/public"
echo
echo "Open the static demo with API-backed data:"
echo "$ROOT/apps/admin/public-demo/index.html?demoApi=http://$HOST:$PORT/demo/public"
echo
echo "Press Ctrl+C to stop."

exec "$PYTHON_BIN" -m uvicorn drivedesk_api.main:app --host "$HOST" --port "$PORT"
