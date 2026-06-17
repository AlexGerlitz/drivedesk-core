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
}
trap cleanup EXIT

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
  LOG_FILE="$(mktemp -t drivedesk-public-demo-api.XXXXXX.log)"
  "$PYTHON_BIN" -m uvicorn drivedesk_api.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --log-level warning \
    >"$LOG_FILE" 2>&1 &
  SERVER_PID="$!"
fi

"$PYTHON_BIN" - <<'PY' "$BASE_URL" "$ROOT/docs/openapi.json"
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

base_url = sys.argv[1].rstrip("/")
openapi_file = Path(sys.argv[2])


def get_json(path: str) -> tuple[dict, dict[str, str]]:
    request = urllib.request.Request(f"{base_url}{path}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
        return payload, headers


def get_text(path: str) -> tuple[str, dict[str, str]]:
    request = urllib.request.Request(f"{base_url}{path}", headers={"Accept": "text/plain"})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = response.read().decode("utf-8")
        headers = {key.lower(): value for key, value in response.headers.items()}
        return payload, headers


deadline = time.monotonic() + 20
last_error: Exception | None = None
while time.monotonic() < deadline:
    try:
        health, _ = get_json("/health")
        if health.get("status") == "ok":
            break
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        last_error = exc
        time.sleep(0.5)
else:
    raise SystemExit(f"API did not become healthy: {last_error}")

health, _ = get_json("/health")
ready, _ = get_json("/ready")
demo, demo_headers = get_json("/demo/public")
openapi, _ = get_json("/openapi.json")
metrics, metrics_headers = get_text("/metrics")

assert health["status"] == "ok", health
assert ready["status"] in {"ready", "degraded"}, ready
assert demo["schemaVersion"] == 1, demo
assert demo["dataSource"] == "api.synthetic", demo
assert demo["apiContract"]["path"] == "/demo/public", demo
assert demo["apiContract"]["data_profile"] == "synthetic_fake_data", demo
assert demo["tenant"]["slug"] == "demo-academy", demo
assert demo["workflow"]["id"] == "wf-demo-lead-to-student", demo
assert demo["workflow"]["currentStage"] == "student_sync", demo
assert len(demo["workflow"]["stages"]) >= 5, demo
assert {stage["state"] for stage in demo["workflow"]["stages"]} >= {"done", "current"}, demo
assert len(demo["timeline"]) >= 5, demo
assert len(demo["domainEvents"]) >= 4, demo
assert {event["event"] for event in demo["domainEvents"]} >= {
    "lead.created",
    "student.created",
    "contract.generated",
    "student.sync.requested",
}
assert len(demo["integrationHealth"]) >= 4, demo
assert {item["state"] for item in demo["integrationHealth"]} >= {
    "processed",
    "retry",
    "dead_letter",
}
assert demo_headers.get("access-control-allow-origin") == "*", demo_headers
assert "public" in demo_headers.get("cache-control", ""), demo_headers
assert metrics_headers.get("content-type", "").startswith("text/plain"), metrics_headers
assert "drivedesk_metrics_storage_available " in metrics, metrics
assert "# HELP drivedesk_auth_sessions Current auth sessions by lifecycle status." in metrics, metrics
assert "# HELP drivedesk_auth_attempts_total Auth attempts grouped by outcome." in metrics, metrics
assert "# HELP drivedesk_business_records Current business records by type and status." in metrics, metrics
assert "# HELP drivedesk_workflow_rules Current workflow rules by status, trigger, and action." in metrics, metrics
assert "# HELP drivedesk_workflow_action_runs Workflow action runs by action type and status." in metrics, metrics
assert "# HELP drivedesk_integration_connections Integration connections by adapter and status." in metrics, metrics
assert "user_email" not in metrics, metrics
assert "token_id" not in metrics, metrics
assert "token_hash" not in metrics, metrics
assert "external_ref" not in metrics, metrics
assert "tenant_id" not in metrics, metrics
assert "/auth/login" in openapi["paths"], openapi["paths"].keys()
assert "/auth/me" in openapi["paths"], openapi["paths"].keys()
assert "/auth/logout" in openapi["paths"], openapi["paths"].keys()
assert "/auth/sessions" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-records" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-records/{record_id}/transition" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/workflow-rules" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/workflow-action-runs" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/outbox-events/{event_id}/retry" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-connections" in openapi["paths"], openapi["paths"].keys()
assert "/demo/public" in openapi["paths"], openapi["paths"].keys()
assert "/health" in openapi["paths"], openapi["paths"].keys()

if openapi_file.exists():
    generated = json.loads(openapi_file.read_text(encoding="utf-8"))
    assert "/demo/public" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/workflow-action-runs" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/outbox-events/{event_id}/retry" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-connections" in generated["paths"], generated["paths"].keys()

print(
    "public demo API contract ok:",
    demo["tenant"]["slug"],
    demo["dataSource"],
    demo["workflow"]["currentStage"],
    len(demo["integrationHealth"]),
)
PY

BASE_URL="$BASE_URL" bash examples/curl/demo-public.sh
BASE_URL="$BASE_URL" "$PYTHON_BIN" examples/python/demo_public_client.py

if command -v node >/dev/null 2>&1; then
  BASE_URL="$BASE_URL" node examples/js/demo-public-fetch.js
else
  echo "node not available; skipped JS demo client"
fi

echo "public demo API smoke ok: $BASE_URL"
