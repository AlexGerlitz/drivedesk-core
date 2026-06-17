#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
API_URL="${BASE_URL%/}/demo/public"

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python is required to validate the response" >&2
  exit 1
fi

payload_file="$(mktemp -t drivedesk-demo-public.XXXXXX.json)"
cleanup() {
  rm -f "$payload_file"
}
trap cleanup EXIT

curl -fsSL "$API_URL" -o "$payload_file"

"$PYTHON_BIN" - <<'PY' "$payload_file"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert payload["schemaVersion"] == 1
assert payload["dataSource"] == "api.synthetic"
assert payload["apiContract"]["path"] == "/demo/public"
assert payload["tenant"]["slug"] == "demo-academy"
assert payload["workflow"]["id"] == "wf-demo-lead-to-student"
assert payload["workflow"]["currentStage"] == "student_sync"
assert len(payload["workflow"]["stages"]) >= 5
assert {event["event"] for event in payload["domainEvents"]} >= {
    "lead.created",
    "student.created",
    "contract.generated",
    "student.sync.requested",
}
assert len(payload["integrationHealth"]) >= 4

print(
    "curl demo client ok:",
    payload["tenant"]["slug"],
    payload["dataSource"],
    f"workflow={payload['workflow']['currentStage']}",
    f"integrationHealth={len(payload['integrationHealth'])}",
)
PY
