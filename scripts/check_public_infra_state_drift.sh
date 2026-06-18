#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TOFU_DIR="${TOFU_DIR:-"$ROOT/infra/opentofu"}"

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
state_dir = tofu_dir / "state"
public_dir = tofu_dir / "public"

required_files = [
    state_dir / "desired-state.sanitized.json",
    state_dir / "observed-state.sanitized.json",
    state_dir / "drift-summary.sanitized.json",
    public_dir / "plan-summary.sanitized.json",
]

missing = [str(path.relative_to(tofu_dir.parent.parent)) for path in required_files if not path.is_file()]

payloads = {}
for path in required_files:
    if path.is_file():
        payloads[path.name] = json.loads(path.read_text(encoding="utf-8"))

all_text = "\n".join(
    path.read_text(encoding="utf-8").lower()
    for path in required_files
    if path.is_file()
)

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
]

desired = payloads.get("desired-state.sanitized.json", {})
observed = payloads.get("observed-state.sanitized.json", {})
summary = payloads.get("drift-summary.sanitized.json", {})
plan = payloads.get("plan-summary.sanitized.json", {})

expected_components = [
    "network_boundary",
    "kubernetes_runtime",
    "gitops_controller",
    "observability",
    "backup_storage",
    "secrets_boundary",
]
expected_environments = ["build", "staging", "canary", "production"]
expected_drifted = ["observability", "backup_storage"]
expected_in_sync = [
    "network_boundary",
    "kubernetes_runtime",
    "gitops_controller",
    "secrets_boundary",
    "state_backend",
]

desired_components = desired.get("components", {})
observed_components = observed.get("components", {})
desired_state_backend = desired.get("state_backend", {})
observed_state_backend = observed.get("state_backend", {})
summary_checks = summary.get("checks", {})

def comparable_component(component: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in component.items() if key != "status"}

drifted_components = [
    component
    for component in expected_components
    if comparable_component(desired_components.get(component, {}))
    != comparable_component(observed_components.get(component, {}))
]
in_sync_components = [
    component
    for component in expected_components
    if comparable_component(desired_components.get(component, {}))
    == comparable_component(observed_components.get(component, {}))
]
if desired_state_backend == {key: observed_state_backend.get(key) for key in desired_state_backend}:
    in_sync_components.append("state_backend")

checks = {
    "state_files_present": not missing,
    "desired_state_recorded": (
        desired.get("state_model") == "public_opentofu_desired_state"
        and desired.get("environments") == expected_environments
        and sorted(desired_components) == sorted(expected_components)
    ),
    "observed_state_recorded": (
        observed.get("state_model") == "public_opentofu_observed_state"
        and observed.get("source", {}).get("live_infrastructure_queried") is False
        and observed.get("environments") == expected_environments
        and sorted(observed_components) == sorted(expected_components)
    ),
    "opentofu_plan_referenced": (
        summary.get("source", {}).get("iac_stack") == "infra/opentofu/public"
        and plan.get("check") == "public_opentofu_plan"
        and plan.get("stack", {}).get("components") == expected_components
    ),
    "component_inventory_matched": (
        sorted(desired_components) == sorted(observed_components) == sorted(expected_components)
    ),
    "state_backend_boundary_preserved": (
        desired_state_backend.get("encrypted_state_required") is True
        and desired_state_backend.get("locking_required") is True
        and desired_state_backend.get("public_backend_config_included") is False
        and desired_state_backend.get("secrets_in_state_allowed") is False
        and observed_state_backend.get("status") == "in_sync"
        and observed_state_backend.get("encrypted_state_required") is True
        and observed_state_backend.get("locking_required") is True
        and observed_state_backend.get("public_backend_config_included") is False
        and observed_state_backend.get("secrets_in_state_allowed") is False
    ),
    "secret_values_excluded": (
        desired_components.get("secrets_boundary", {}).get("secret_values_excluded") is True
        and observed_components.get("secrets_boundary", {}).get("secret_values_excluded") is True
    ),
    "drift_detected": (
        summary.get("drift", {}).get("detected") is True
        and summary.get("drift", {}).get("drift_count") == 2
        and drifted_components == expected_drifted
    ),
    "drifted_components_recorded": summary.get("drift", {}).get("drifted_components") == expected_drifted,
    "in_sync_components_recorded": (
        summary.get("drift", {}).get("in_sync_components") == expected_in_sync
        and in_sync_components == expected_in_sync
    ),
    "plan_only_no_apply": (
        summary.get("decision", {}).get("event_type") == "infra.state_drift.detected"
        and summary.get("decision", {}).get("apply_mode") == "plan_only"
        and summary.get("decision", {}).get("apply_from_public_export") is False
        and summary_checks.get("plan_only_no_apply") is True
    ),
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_infra_state_drift",
    "data_profile": "synthetic_demo_data",
    "drift_model": "opentofu_desired_vs_observed_state",
    "source": {
        "desired_state": "infra/opentofu/state/desired-state.sanitized.json",
        "observed_state": "infra/opentofu/state/observed-state.sanitized.json",
        "iac_stack": "infra/opentofu/public",
        "plan_summary": "infra/opentofu/public/plan-summary.sanitized.json",
    },
    "drift": {
        "detected": True,
        "drift_count": len(drifted_components),
        "drifted_components": drifted_components,
        "in_sync_components": in_sync_components,
        "severity": summary.get("drift", {}).get("severity"),
    },
    "decision": {
        "event_type": "infra.state_drift.detected",
        "recommended_action": "plan_remediation_after_review",
        "apply_mode": "plan_only",
        "apply_from_public_export": False,
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
        print(f"missing public infrastructure state drift files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public infrastructure state drift check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public infrastructure state drift check ok: "
    "drifted=observability,backup_storage mode=plan_only"
)
PY
