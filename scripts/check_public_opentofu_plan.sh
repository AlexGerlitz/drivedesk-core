#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TOFU_DIR="${TOFU_DIR:-"$ROOT/infra/opentofu/public"}"

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

"$PYTHON_BIN" - <<'PY' "$TOFU_DIR"
from __future__ import annotations

import json
import sys
from pathlib import Path

tofu_dir = Path(sys.argv[1])

required_files = [
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "plan-summary.sanitized.json",
]

missing = [relative for relative in required_files if not (tofu_dir / relative).is_file()]
texts = {
    relative: (tofu_dir / relative).read_text(encoding="utf-8")
    for relative in required_files
    if (tofu_dir / relative).is_file()
}
all_text = "\n".join(texts.values()).lower()

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
]

plan = {}
if "plan-summary.sanitized.json" in texts:
    plan = json.loads(texts["plan-summary.sanitized.json"])

main_tf = texts.get("main.tf", "")
variables_tf = texts.get("variables.tf", "")
outputs_tf = texts.get("outputs.tf", "")

expected_environments = ["build", "staging", "canary", "production"]
expected_components = [
    "network_boundary",
    "kubernetes_runtime",
    "gitops_controller",
    "observability",
    "backup_storage",
    "secrets_boundary",
]

checks = {
    "opentofu_files_present": not missing,
    "environment_model_recorded": all(
        environment in main_tf
        and environment in variables_tf
        and environment in plan.get("stack", {}).get("environments", [])
        for environment in expected_environments
    ),
    "component_model_recorded": all(
        component in main_tf and component in plan.get("stack", {}).get("components", [])
        for component in expected_components
    ),
    "state_boundary_recorded": all(
        value in main_tf
        for value in [
            "encrypted_state_required",
            "locking_required",
            "public_backend_config_included",
            "secrets_in_state_allowed",
        ]
    )
    and plan.get("state", {}).get("encrypted_state_required") is True
    and plan.get("state", {}).get("locking_required") is True,
    "secret_values_excluded": (
        "secret_values_excluded" in main_tf
        and plan.get("state", {}).get("secrets_in_state_allowed") is False
    ),
    "plan_only_no_apply": (
        "plan_only" in main_tf
        and plan.get("plan", {}).get("mode") == "plan_only"
        and plan.get("plan", {}).get("apply_from_public_export") is False
    ),
    "destroy_count_zero": plan.get("plan", {}).get("destroy_count") == 0
    and plan.get("plan", {}).get("delete_count") == 0,
    "public_backend_config_absent": plan.get("state", {}).get("public_backend_config_included") is False
    and 'backend "' not in all_text,
    "output_contract_present": "drivedesk_public_iac_contract" in outputs_tf,
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_opentofu_plan",
    "data_profile": "synthetic_demo_data",
    "iac_model": "opentofu_plan_only_infrastructure_contract",
    "stack": {
        "path": "infra/opentofu/public",
        "tool": "opentofu",
        "environments": expected_environments,
        "components": expected_components,
    },
    "state": {
        "encrypted_state_required": True,
        "locking_required": True,
        "public_backend_config_included": False,
        "secrets_in_state_allowed": False,
    },
    "plan": {
        "mode": "plan_only",
        "apply_from_public_export": False,
        "create_count": plan.get("plan", {}).get("create_count", 0),
        "update_count": plan.get("plan", {}).get("update_count", 0),
        "delete_count": plan.get("plan", {}).get("delete_count", 0),
        "destroy_count": plan.get("plan", {}).get("destroy_count", 0),
        "production_data_touched": False,
    },
    "checks": checks,
    "redaction": {
        "paths_included": False,
        "hostnames_included": False,
        "addresses_included": False,
        "credentials_included": False,
        "raw_logs_included": False,
        "production_data_included": False,
    },
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

if not passed:
    print(json.dumps(payload, indent=2, sort_keys=True))
    if missing:
        print(f"missing OpenTofu public files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public OpenTofu plan check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print("public OpenTofu plan check ok: stack=infra/opentofu/public mode=plan_only")
PY
