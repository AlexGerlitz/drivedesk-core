#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

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

TEMP_DIR="$(mktemp -d -t drivedesk-public-demo-sdk.XXXXXX)"
SERVER_PID=""
LOG_FILE=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$LOG_FILE" && -f "$LOG_FILE" ]]; then
    rm -f "$LOG_FILE"
  fi
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

OPENAPI_FILE="${DRIVEDESK_PUBLIC_OPENAPI_FILE:-$ROOT/docs/openapi.json}"
if [[ ! -f "$OPENAPI_FILE" ]]; then
  OPENAPI_FILE="$TEMP_DIR/openapi.json"
  "$PYTHON_BIN" - <<'PY' > "$OPENAPI_FILE"
from __future__ import annotations

import json

from drivedesk_api.main import build_app

print(json.dumps(build_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True))
PY
fi

GENERATED_DIR="$TEMP_DIR/public-demo"
"$PYTHON_BIN" scripts/generate_public_demo_sdk.py \
  --openapi "$OPENAPI_FILE" \
  --out "$GENERATED_DIR"

if [[ ! -d "$ROOT/sdk/generated/public-demo" ]]; then
  echo "missing committed generated SDK: sdk/generated/public-demo" >&2
  exit 1
fi

diff -ru "$ROOT/sdk/generated/public-demo" "$GENERATED_DIR"

if [[ -n "${DRIVEDESK_DEMO_BASE_URL:-}" ]]; then
  BASE_URL="${DRIVEDESK_DEMO_BASE_URL%/}"
else
  PORT="${DRIVEDESK_DEMO_API_PORT:-}"
  if [[ -z "$PORT" ]]; then
    PORT="$("$PYTHON_BIN" - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
  fi
  BASE_URL="http://127.0.0.1:$PORT"
  LOG_FILE="$(mktemp -t drivedesk-public-demo-sdk-api.XXXXXX.log)"
  "$PYTHON_BIN" -m uvicorn drivedesk_api.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --log-level warning \
    >"$LOG_FILE" 2>&1 &
  SERVER_PID="$!"
fi

"$PYTHON_BIN" - <<'PY' "$BASE_URL"
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
deadline = time.monotonic() + 20
last_error: Exception | None = None

while time.monotonic() < deadline:
    try:
        request = urllib.request.Request(f"{base_url}/health", headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("status") == "ok":
            break
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        last_error = exc
        time.sleep(0.5)
else:
    raise SystemExit(f"API did not become healthy: {last_error}")
PY

"$PYTHON_BIN" sdk/generated/public-demo/python/drivedesk_public_demo_client.py --base-url "$BASE_URL"

if command -v node >/dev/null 2>&1; then
  node sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs --base-url "$BASE_URL"
else
  echo "node not available; skipped generated JS SDK client"
fi

echo "public demo SDK smoke ok: $BASE_URL"
