#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
VALIDATION_DIR="${VALIDATION_DIR:-"$ROOT/infra/state-validation"}"
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

"$PYTHON_BIN" - <<'PY' "$VALIDATION_DIR" "$PUBLIC_DOCS" "$ROOT"
from __future__ import annotations

import json
import sys
from pathlib import Path

validation_dir = Path(sys.argv[1])
public_docs = Path(sys.argv[2])
root = Path(sys.argv[3])

contract_path = validation_dir / "private-infra-validation.sanitized.json"
evidence_path = public_docs / "evidence/private-infra-validation.sanitized.json"
staging_path = public_docs / "evidence/de-staging-evidence.sanitized.json"
opentofu_plan_path = root / "infra/opentofu/public/plan-summary.sanitized.json"
infra_drift_path = root / "infra/opentofu/state/drift-summary.sanitized.json"
runtime_rollout_path = public_docs / "evidence/runtime-rollout.sanitized.json"
gitops_layout_path = public_docs / "evidence/gitops-layout.sanitized.json"

required_files = [
    contract_path,
    evidence_path,
    staging_path,
    opentofu_plan_path,
    infra_drift_path,
    runtime_rollout_path,
    gitops_layout_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": contract_path,
    "evidence": evidence_path,
    "staging": staging_path,
    "opentofu_plan": opentofu_plan_path,
    "infra_drift": infra_drift_path,
    "runtime_rollout": runtime_rollout_path,
    "gitops_layout": gitops_layout_path,
}.items():
    if path.is_file():
        payloads[key] = json.loads(path.read_text(encoding="utf-8"))

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

contract = payloads.get("contract", {})
evidence = payloads.get("evidence", {})
staging = payloads.get("staging", {})
opentofu_plan = payloads.get("opentofu_plan", {})
infra_drift = payloads.get("infra_drift", {})
runtime_rollout = payloads.get("runtime_rollout", {})
gitops_layout = payloads.get("gitops_layout", {})

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
    "gitops_manifests",
    "opentofu_contract",
]

source_contracts = set(contract.get("source_contracts", []))
expected_sources = {
    "infra/opentofu/public/plan-summary.sanitized.json",
    "infra/opentofu/state/drift-summary.sanitized.json",
    "infra/runtime-rollout/private-staging-rollout.sanitized.json",
    "docs/public/evidence/gitops-layout.sanitized.json",
    "docs/public/evidence/de-staging-evidence.sanitized.json",
}

collector = contract.get("collector", {})
boundaries = contract.get("boundaries", {})
evidence_checks = evidence.get("checks", {})

checks = {
    "validation_files_present": not missing,
    "validation_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("validation_model") == "private_control_plane_state_validation"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
    ),
    "evidence_contract_present": (
        evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_validation"
        and evidence.get("validation_model") == "private_control_plane_state_validation"
        and evidence.get("data_profile") == "sanitized_private_staging_summary"
    ),
    "read_only_collector_recorded": (
        collector.get("mode") == "read_only"
        and collector.get("raw_output_retention") == "private_only"
        and collector.get("sanitized_public_output") is True
        and evidence_checks.get("read_only_collector_recorded") is True
    ),
    "no_runtime_mutation_recorded": (
        collector.get("mutates_runtime") is False
        and collector.get("restarts_services") is False
        and collector.get("applies_infrastructure") is False
        and evidence_checks.get("no_runtime_mutation_recorded") is True
    ),
    "source_contracts_referenced": (
        source_contracts == expected_sources
        and evidence_checks.get("source_contracts_referenced") is True
        and evidence.get("source", {}).get("validation_contract")
        == "infra/state-validation/private-infra-validation.sanitized.json"
    ),
    "staging_evidence_referenced": (
        staging.get("checks", {}).get("ci_success") is True
        and staging.get("checks", {}).get("deploy_success") is True
        and staging.get("checks", {}).get("health_success") is True
        and staging.get("checks", {}).get("evidence_success") is True
        and evidence_checks.get("staging_evidence_referenced") is True
    ),
    "component_inventory_recorded": (
        contract.get("components") == expected_components
        and evidence.get("components") == expected_components
    ),
    "runtime_components_validated": (
        staging.get("checks", {}).get("api_health_ok") is True
        and staging.get("checks", {}).get("api_ready_ok") is True
        and staging.get("checks", {}).get("api_metrics_ok") is True
        and staging.get("checks", {}).get("readiness_metrics_ok") is True
        and staging.get("checks", {}).get("http_metrics_ok") is True
        and staging.get("checks", {}).get("outbox_metrics_ok") is True
        and {"api", "worker", "postgresql", "redis"}.issubset(
            set(runtime_rollout.get("components", []))
        )
        and evidence_checks.get("runtime_components_validated") is True
    ),
    "observability_state_validated": (
        staging.get("checks", {}).get("prometheus_required_targets_up") is True
        and staging.get("checks", {}).get("prometheus_alert_rules_ok") is True
        and staging.get("checks", {}).get("loki_query_ok") is True
        and staging.get("checks", {}).get("alertmanager_ready_ok") is True
        and staging.get("checks", {}).get("grafana_dashboard_ok") is True
        and evidence_checks.get("observability_state_validated") is True
    ),
    "opentofu_contract_referenced": (
        opentofu_plan.get("check") == "public_opentofu_plan"
        and infra_drift.get("check") == "public_infra_state_drift"
        and infra_drift.get("decision", {}).get("apply_mode") == "plan_only"
        and evidence_checks.get("opentofu_contract_referenced") is True
    ),
    "gitops_contract_referenced": (
        gitops_layout.get("check") == "public_gitops_layout"
        and gitops_layout.get("gitops", {}).get("controller") == "argocd"
        and evidence_checks.get("gitops_contract_referenced") is True
    ),
    "runtime_rollout_referenced": (
        runtime_rollout.get("check") == "public_runtime_rollout_evidence"
        and runtime_rollout.get("checks", {}).get("staging_deploy_success") is True
        and runtime_rollout.get("checks", {}).get("staging_health_success") is True
        and evidence_checks.get("runtime_rollout_referenced") is True
    ),
    "loopback_boundary_recorded": (
        boundaries.get("loopback_only") is True
        and staging.get("checks", {}).get("api_private_listener") is True
        and staging.get("checks", {}).get("prometheus_private_listener") is True
        and staging.get("checks", {}).get("grafana_private_listener") is True
        and evidence_checks.get("loopback_boundary_recorded") is True
    ),
    "public_route_disabled": (
        contract.get("environment", {}).get("public_route") is False
        and evidence.get("environment", {}).get("public_route") is False
        and staging.get("runtime", {}).get("public_route") is False
        and evidence_checks.get("public_route_disabled") is True
    ),
    "redaction_boundary_recorded": (
        boundaries.get("no_raw_logs") is True
        and boundaries.get("no_request_bodies") is True
        and boundaries.get("no_credentials") is True
        and boundaries.get("no_private_paths") is True
        and boundaries.get("no_addresses") is True
        and evidence.get("redaction", {}).get("paths_included") is False
        and evidence.get("redaction", {}).get("hostnames_included") is False
        and evidence.get("redaction", {}).get("addresses_included") is False
        and evidence.get("redaction", {}).get("credentials_included") is False
        and evidence.get("redaction", {}).get("raw_logs_included") is False
        and evidence.get("redaction", {}).get("request_bodies_included") is False
        and evidence.get("redaction", {}).get("production_data_included") is False
        and evidence_checks.get("redaction_boundary_recorded") is True
    ),
    "operator_review_required": (
        contract.get("rollback", {}).get("operator_review_required") is True
        and contract.get("decision", {}).get("operator_review_required") is True
        and evidence.get("decision", {}).get("operator_review_required") is True
        and evidence.get("decision", {}).get("automatic_public_apply") is False
        and evidence_checks.get("operator_review_required") is True
    ),
    "validation_event_recorded": evidence.get("decision", {}).get("event_type") == "infra.private_state.validated",
    "private_markers_absent": (
        not any(marker in all_text for marker in private_markers)
        and evidence_checks.get("private_markers_absent") is True
    ),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_private_infra_validation",
    "data_profile": "sanitized_private_staging_summary",
    "validation_model": "private_control_plane_state_validation",
    "source": {
        "validation_contract": "infra/state-validation/private-infra-validation.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
        "opentofu_plan": "infra/opentofu/public/plan-summary.sanitized.json",
        "infra_state_drift": "infra/opentofu/state/drift-summary.sanitized.json",
        "runtime_rollout": "docs/public/evidence/runtime-rollout.sanitized.json",
        "gitops_layout": "docs/public/evidence/gitops-layout.sanitized.json",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "components": expected_components,
    "checks": checks,
    "decision": {
        "event_type": "infra.private_state.validated",
        "recommended_action": "continue_with_reviewed_plan_before_apply",
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
        print(f"missing public private infra validation files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public private infra validation check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print("public private infra validation check ok: environment=private_staging mode=read_only event=infra.private_state.validated")
PY
