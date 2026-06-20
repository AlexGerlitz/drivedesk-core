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

from drivedesk_core import build_provider_sandbox_dry_run_plan


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

print(
    "public provider sandbox dry-run check ok: "
    f"adapter={ready['adapter_key']} status={ready['status']} operation={ready['request_plan']['operation']}"
)
PY
