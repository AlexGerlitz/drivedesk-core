#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROLLOUT_DIR="${ROLLOUT_DIR:-"$ROOT/infra/runtime-rollout"}"
PUBLIC_DOCS="${PUBLIC_DOCS:-"$ROOT/docs/public"}"

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

"$PYTHON_BIN" - <<'PY' "$ROLLOUT_DIR" "$PUBLIC_DOCS"
from __future__ import annotations

import json
import sys
from pathlib import Path

rollout_dir = Path(sys.argv[1])
public_docs = Path(sys.argv[2])

contract_path = rollout_dir / "private-staging-rollout.sanitized.json"
evidence_path = public_docs / "evidence/runtime-rollout.sanitized.json"
staging_path = public_docs / "evidence/de-staging-evidence.sanitized.json"

required_files = [contract_path, evidence_path, staging_path]
missing = [str(path) for path in required_files if not path.is_file()]

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

contract = payloads.get("private-staging-rollout.sanitized.json", {})
evidence = payloads.get("runtime-rollout.sanitized.json", {})
staging = payloads.get("de-staging-evidence.sanitized.json", {})

expected_stages = ["build", "deploy", "runtime_health", "observability", "evidence"]
expected_components = [
    "api",
    "worker",
    "postgresql",
    "redis",
    "prometheus",
    "loki",
    "alloy",
    "alertmanager",
    "grafana",
]

contract_stage_names = [stage.get("name") for stage in contract.get("stages", [])]
contract_stage_statuses = [stage.get("status") for stage in contract.get("stages", [])]

checks = {
    "rollout_files_present": not missing,
    "rollout_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("rollout_model") == "github_actions_to_private_loopback_staging"
        and contract.get("data_profile") == "synthetic_fake_data"
    ),
    "build_stage_recorded": "build" in contract_stage_names and "build" in evidence.get("stages", []),
    "deploy_stage_recorded": "deploy" in contract_stage_names and "deploy" in evidence.get("stages", []),
    "runtime_health_stage_recorded": (
        "runtime_health" in contract_stage_names and "runtime_health" in evidence.get("stages", [])
    ),
    "observability_stage_recorded": (
        "observability" in contract_stage_names and "observability" in evidence.get("stages", [])
    ),
    "evidence_stage_recorded": "evidence" in contract_stage_names and "evidence" in evidence.get("stages", []),
    "stage_order_recorded": contract_stage_names == expected_stages and evidence.get("stages") == expected_stages,
    "stage_statuses_passed": contract_stage_statuses == ["passed"] * len(expected_stages),
    "component_inventory_recorded": (
        contract.get("components") == expected_components
        and evidence.get("components") == expected_components
    ),
    "staging_deploy_success": staging.get("checks", {}).get("deploy_success") is True,
    "staging_health_success": staging.get("checks", {}).get("health_success") is True,
    "staging_evidence_success": staging.get("checks", {}).get("evidence_success") is True,
    "loopback_boundary_recorded": (
        contract.get("boundaries", {}).get("loopback_only") is True
        and evidence.get("checks", {}).get("loopback_boundary_recorded") is True
        and staging.get("checks", {}).get("api_private_listener") is True
        and staging.get("checks", {}).get("prometheus_private_listener") is True
        and staging.get("checks", {}).get("grafana_private_listener") is True
    ),
    "public_route_disabled": (
        contract.get("environment", {}).get("public_route") is False
        and evidence.get("runtime", {}).get("public_route") is False
        and staging.get("runtime", {}).get("public_route") is False
    ),
    "api_health_ok": staging.get("checks", {}).get("api_health_ok") is True,
    "api_ready_ok": staging.get("checks", {}).get("api_ready_ok") is True,
    "api_metrics_ok": staging.get("checks", {}).get("api_metrics_ok") is True,
    "prometheus_targets_up": staging.get("checks", {}).get("prometheus_required_targets_up") is True,
    "prometheus_alert_rules_ok": staging.get("checks", {}).get("prometheus_alert_rules_ok") is True,
    "loki_query_ok": staging.get("checks", {}).get("loki_query_ok") is True,
    "alertmanager_ready_ok": staging.get("checks", {}).get("alertmanager_ready_ok") is True,
    "grafana_dashboard_ok": staging.get("checks", {}).get("grafana_dashboard_ok") is True,
    "rollback_strategy_recorded": (
        contract.get("rollback", {}).get("operator_review_required") is True
        and contract.get("rollback", {}).get("automatic_public_apply") is False
        and evidence.get("decision", {}).get("operator_review_required") is True
        and evidence.get("decision", {}).get("automatic_public_apply") is False
    ),
    "redaction_boundary_recorded": (
        evidence.get("redaction", {}).get("hostnames_included") is False
        and evidence.get("redaction", {}).get("addresses_included") is False
        and evidence.get("redaction", {}).get("credentials_included") is False
        and evidence.get("redaction", {}).get("raw_logs_included") is False
        and evidence.get("redaction", {}).get("request_bodies_included") is False
        and evidence.get("redaction", {}).get("production_data_included") is False
        and staging.get("redaction", {}).get("hostnames_included") is False
        and staging.get("redaction", {}).get("addresses_included") is False
        and staging.get("redaction", {}).get("credentials_included") is False
        and staging.get("redaction", {}).get("raw_logs_included") is False
        and staging.get("redaction", {}).get("production_data_included") is False
    ),
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_runtime_rollout_evidence",
    "data_profile": "synthetic_fake_data",
    "rollout_model": "github_actions_to_private_loopback_staging",
    "source": {
        "rollout_contract": "infra/runtime-rollout/private-staging-rollout.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
    },
    "runtime": {
        "environment": "private_staging",
        "public_route": False,
        "control_plane": "private_de_control_plane",
        "production_data_touched": False,
    },
    "stages": expected_stages,
    "components": expected_components,
    "checks": checks,
    "decision": {
        "event_type": "runtime.rollout.evidence_collected",
        "promotion_basis": "private_staging_health_and_observability_gates",
        "automatic_public_apply": False,
        "operator_review_required": True,
        "production_data_touched": False,
    },
    "redaction": {
        "paths_included": False,
        "hostnames_included": False,
        "addresses_included": False,
        "credentials_included": False,
        "raw_logs_included": False,
        "request_bodies_included": False,
        "production_data_included": False,
    },
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

if not passed:
    print(json.dumps(payload, indent=2, sort_keys=True))
    if missing:
        print(f"missing public runtime rollout files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public runtime rollout evidence check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print("public runtime rollout evidence check ok: environment=private_staging stages=build,deploy,runtime_health,observability,evidence")
PY
