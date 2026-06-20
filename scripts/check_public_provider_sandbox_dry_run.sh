#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-}"

cd "$ROOT"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi
fi

PYTHONPATH="packages/core" "$PYTHON_BIN" - <<'PY'
import json

from drivedesk_core import build_provider_sandbox_dry_run_plan, execute_provider_sandbox_dry_run


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


blocked = build_provider_sandbox_dry_run_plan("crm.bitrix24.mock", env={})
require(blocked["status"] == "blocked_missing_secret_binding", "missing env should block dry-run")
require(blocked["provider_call_enabled"] is False, "provider call must default to disabled")
require(blocked["external_mutation"] is False, "sandbox dry-run must not mutate provider")
require(blocked["secret_values_included"] is False, "secret values must never be included")
require(
    set(blocked["missing_secret_refs"]) == {"BITRIX24_WEBHOOK_URL", "BITRIX24_CLIENT_SECRET"},
    "missing secret refs mismatch",
)
require(blocked["missing_config_refs"] == ["BITRIX24_TENANT_DOMAIN"], "missing config refs mismatch")
require(blocked["request_plan"]["operation"] == "crm.deal.list", "unexpected provider operation")
require(blocked["request_plan"]["max_page_size"] == 5, "dry-run page size must stay bounded")
require(blocked["request_plan"]["external_mutation"] is False, "request plan must be read-only")
require(
    {"secret_refs_bound", "tenant_domain_bound", "provider_call_lock", "write_lock"}.issubset(
        {gate["gate"] for gate in blocked["gates"]}
    ),
    "sandbox gates incomplete",
)

secret_env = {
    "BITRIX24_CLIENT_SECRET": "client-secret-value",
    "BITRIX24_WEBHOOK_URL": "https://example.invalid/rest/1/secret-token",
    "BITRIX24_TENANT_DOMAIN": "tenant.bitrix24.invalid",
}
ready = build_provider_sandbox_dry_run_plan("crm.bitrix24.mock", env=secret_env)
ready_json = json.dumps(ready, sort_keys=True)
require(
    ready["status"] == "ready_for_private_read_only_dry_run",
    "bound refs should prepare private read-only dry-run",
)
require(ready["missing_secret_refs"] == [], "secret refs should be bound")
require(ready["missing_config_refs"] == [], "config refs should be bound")
require(ready["provider_call_enabled"] is False, "public-safe plan must still disable provider call")
require(ready["request_plan"]["provider_call_enabled"] is False, "request plan call flag mismatch")
require("client-secret-value" not in ready_json, "client secret leaked")
require("secret-token" not in ready_json, "webhook token leaked")
require("tenant.bitrix24.invalid" not in ready_json, "tenant domain value leaked")

call_prepared = build_provider_sandbox_dry_run_plan(
    "crm.bitrix24.mock",
    env=secret_env,
    allow_provider_call=True,
)
call_json = json.dumps(call_prepared, sort_keys=True)
require(call_prepared["status"] == "provider_call_prepared", "provider call opt-in status mismatch")
require(call_prepared["provider_call_enabled"] is True, "provider call opt-in should be visible")
require(call_prepared["external_mutation"] is False, "provider dry-run must stay read-only")
require("client-secret-value" not in call_json, "client secret leaked in opt-in plan")
require("secret-token" not in call_json, "webhook token leaked in opt-in plan")
require("tenant.bitrix24.invalid" not in call_json, "tenant domain leaked in opt-in plan")

transport_calls = []


def fake_transport(request):
    transport_calls.append(request)
    return {
        "result": [
            {
                "ID": "DEAL-2026-100",
                "STAGE_ID": "NEW",
                "ASSIGNED_BY_ID": "7",
                "OPPORTUNITY": "1500",
                "PHONE": "+70000000000",
                "CLIENT_NAME": "Hidden Person",
                "access_token": "secret-token",
            },
            {
                "ID": "",
                "STAGE_ID": "BROKEN",
                "EMAIL": "hidden@example.invalid",
            },
        ],
        "total": 2,
    }


locked_runner = execute_provider_sandbox_dry_run(
    "crm.bitrix24.mock",
    env=secret_env,
    allow_provider_call=False,
    provider_transport=fake_transport,
)
require(locked_runner["status"] == "provider_call_disabled", "runner must lock provider call by default")
require(transport_calls == [], "runner called provider while disabled")

runner = execute_provider_sandbox_dry_run(
    "crm.bitrix24.mock",
    env=secret_env,
    allow_provider_call=True,
    provider_transport=fake_transport,
)
runner_json = json.dumps(runner, sort_keys=True)
require(runner["status"] == "private_read_only_dry_run_completed", "runner completion status mismatch")
require(runner["records_received"] == 2, "runner received count mismatch")
require(runner["records_accepted"] == 1, "runner accepted count mismatch")
require(runner["records_rejected"] == 1, "runner rejected count mismatch")
require(runner["provider_reported_total"] == 2, "runner total mismatch")
require(runner["accepted_subject_ref_count"] == 1, "runner subject ref count mismatch")
require(runner["reconciliation_probe_attached"] is True, "runner must attach reconciliation probe")
require(runner["external_mutation"] is False, "runner must stay read-only")
require(runner["raw_payload_included"] is False, "runner must not include raw payload")
require(runner["provider_endpoint_included"] is False, "runner must not include provider endpoint")
require(runner["secret_values_included"] is False, "runner must not include secret values")
require(len(transport_calls) == 1, "runner transport call count mismatch")
require(transport_calls[0]["method"] == "POST", "runner method mismatch")
require(transport_calls[0]["json"]["start"] == 0, "runner pagination start mismatch")
for leaked in [
    "client-secret-value",
    "secret-token",
    "tenant.bitrix24.invalid",
    "+70000000000",
    "Hidden Person",
    "hidden@example.invalid",
    "DEAL-2026-100",
]:
    require(leaked not in runner_json, f"runner leaked value: {leaked}")


def failing_transport(request):
    raise RuntimeError(f"provider URL leaked in exception: {request['url']}")


retryable = execute_provider_sandbox_dry_run(
    "crm.bitrix24.mock",
    env=secret_env,
    allow_provider_call=True,
    provider_transport=failing_transport,
)
retryable_json = json.dumps(retryable, sort_keys=True)
require(
    retryable["status"] == "private_read_only_dry_run_retryable_failure",
    "runner retryable failure status mismatch",
)
require(retryable["failure"]["error_message_included"] is False, "runner must redact exception message")
require("secret-token" not in retryable_json, "runner leaked webhook token in retryable failure")

print(
    "public provider sandbox dry-run check ok: "
    f"adapter={ready['adapter_key']} status={ready['status']} "
    f"runner={runner['status']} operation={ready['request_plan']['operation']}"
)
PY

cli_plan="$(
  BITRIX24_CLIENT_SECRET="client-secret-value" \
  BITRIX24_WEBHOOK_URL="https://example.invalid/rest/1/secret-token" \
  BITRIX24_TENANT_DOMAIN="tenant.bitrix24.invalid" \
  PYTHONPATH="packages/core" "$PYTHON_BIN" scripts/run_provider_sandbox_dry_run.py --plan-only
)"

if [[ "$cli_plan" != *"ready_for_private_read_only_dry_run"* ]]; then
  echo "provider sandbox dry-run CLI plan did not reach ready state" >&2
  exit 1
fi

if [[ "$cli_plan" == *"client-secret-value"* || "$cli_plan" == *"secret-token"* || "$cli_plan" == *"tenant.bitrix24.invalid"* ]]; then
  echo "provider sandbox dry-run CLI leaked secret/config values in plan-only mode" >&2
  exit 1
fi

cli_fake="$(
  BITRIX24_CLIENT_SECRET="client-secret-value" \
  BITRIX24_WEBHOOK_URL="https://example.invalid/rest/1/secret-token" \
  BITRIX24_TENANT_DOMAIN="tenant.bitrix24.invalid" \
  PYTHONPATH="packages/core" "$PYTHON_BIN" scripts/run_provider_sandbox_dry_run.py --execute-read-only --transport fake
)"

if [[ "$cli_fake" != *"private_read_only_dry_run_completed"* ]]; then
  echo "provider sandbox dry-run CLI fake transport did not complete" >&2
  exit 1
fi

for leaked in \
  "client-secret-value" \
  "secret-token" \
  "tenant.bitrix24.invalid" \
  "+70000000000" \
  "Hidden Person" \
  "hidden@example.invalid" \
  "DEAL-PRIVATE-DRY-RUN-001"; do
  if [[ "$cli_fake" == *"$leaked"* ]]; then
    echo "provider sandbox dry-run CLI leaked value: $leaked" >&2
    exit 1
  fi
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
evidence_file="$tmp_dir/provider-sandbox.sanitized.json"

BITRIX24_CLIENT_SECRET="client-secret-value" \
BITRIX24_WEBHOOK_URL="https://example.invalid/rest/1/secret-token" \
BITRIX24_TENANT_DOMAIN="tenant.bitrix24.invalid" \
MODE="execute-read-only" \
TRANSPORT="fake" \
OUTPUT="$evidence_file" \
PYTHON_BIN="$PYTHON_BIN" \
bash scripts/record_provider_sandbox_dry_run_evidence.sh >/dev/null

"$PYTHON_BIN" scripts/check_provider_sandbox_dry_run_evidence.py "$evidence_file" --require-completed

recorded="$(cat "$evidence_file")"
if [[ "$recorded" != *"private_read_only_dry_run_completed"* ]]; then
  echo "provider sandbox recorded evidence missing completed status" >&2
  exit 1
fi

for leaked in \
  "client-secret-value" \
  "secret-token" \
  "tenant.bitrix24.invalid" \
  "+70000000000" \
  "Hidden Person" \
  "hidden@example.invalid" \
  "DEAL-PRIVATE-DRY-RUN-001"; do
  if [[ "$recorded" == *"$leaked"* ]]; then
    echo "provider sandbox recorded evidence leaked value: $leaked" >&2
    exit 1
  fi
done
