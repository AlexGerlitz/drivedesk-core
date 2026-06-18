#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REMEDIATION_DIR="${REMEDIATION_DIR:-"$ROOT/infra/state-remediation"}"
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

"$PYTHON_BIN" - <<'PY' "$REMEDIATION_DIR" "$PUBLIC_DOCS" "$ROOT"
from __future__ import annotations

import json
import sys
from pathlib import Path

remediation_dir = Path(sys.argv[1])
public_docs = Path(sys.argv[2])
root = Path(sys.argv[3])

contract_path = remediation_dir / "private-infra-remediation-plan.sanitized.json"
evidence_path = public_docs / "evidence/private-infra-remediation-plan.sanitized.json"
validation_contract_path = root / "infra/state-validation/private-infra-validation.sanitized.json"
validation_evidence_path = public_docs / "evidence/private-infra-validation.sanitized.json"
infra_drift_path = root / "infra/opentofu/state/drift-summary.sanitized.json"
opentofu_plan_path = root / "infra/opentofu/public/plan-summary.sanitized.json"
runtime_rollout_path = public_docs / "evidence/runtime-rollout.sanitized.json"
gitops_remediation_path = public_docs / "evidence/gitops-drift-remediation.sanitized.json"
staging_evidence_path = public_docs / "evidence/de-staging-evidence.sanitized.json"

required_files = [
    contract_path,
    evidence_path,
    validation_contract_path,
    validation_evidence_path,
    infra_drift_path,
    opentofu_plan_path,
    runtime_rollout_path,
    gitops_remediation_path,
    staging_evidence_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": contract_path,
    "evidence": evidence_path,
    "validation_contract": validation_contract_path,
    "validation_evidence": validation_evidence_path,
    "infra_drift": infra_drift_path,
    "opentofu_plan": opentofu_plan_path,
    "runtime_rollout": runtime_rollout_path,
    "gitops_remediation": gitops_remediation_path,
    "staging_evidence": staging_evidence_path,
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
validation_contract = payloads.get("validation_contract", {})
validation_evidence = payloads.get("validation_evidence", {})
infra_drift = payloads.get("infra_drift", {})
opentofu_plan = payloads.get("opentofu_plan", {})
runtime_rollout = payloads.get("runtime_rollout", {})
gitops_remediation = payloads.get("gitops_remediation", {})
staging_evidence = payloads.get("staging_evidence", {})

expected_sources = {
    "infra/state-validation/private-infra-validation.sanitized.json",
    "docs/public/evidence/private-infra-validation.sanitized.json",
    "infra/opentofu/state/drift-summary.sanitized.json",
    "infra/opentofu/public/plan-summary.sanitized.json",
    "infra/runtime-rollout/private-staging-rollout.sanitized.json",
    "docs/public/evidence/runtime-rollout.sanitized.json",
    "docs/public/evidence/gitops-drift-remediation.sanitized.json",
    "docs/public/evidence/de-staging-evidence.sanitized.json",
}

contract_sources = set(contract.get("source_contracts", []))
evidence_source = evidence.get("source", {})
expected_drifted_components = ["observability", "backup_storage"]
actions = contract.get("remediation_plan", {}).get("actions", [])
action_by_component = {action.get("component"): action for action in actions}
evidence_checks = evidence.get("checks", {})
boundaries = contract.get("boundaries", {})
planner = contract.get("planner", {})

checks = {
    "remediation_files_present": not missing,
    "remediation_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("remediation_model") == "private_control_plane_remediation_plan"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
        and evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_remediation_plan"
        and evidence.get("remediation_model") == "private_control_plane_remediation_plan"
        and evidence_checks.get("remediation_contract_present") is True
    ),
    "validation_evidence_referenced": (
        validation_contract.get("validation_model") == "private_control_plane_state_validation"
        and validation_evidence.get("check") == "public_private_infra_validation"
        and validation_evidence.get("decision", {}).get("event_type") == "infra.private_state.validated"
        and evidence_source.get("validation_contract")
        == "infra/state-validation/private-infra-validation.sanitized.json"
        and evidence_source.get("validation_evidence")
        == "docs/public/evidence/private-infra-validation.sanitized.json"
        and evidence_checks.get("validation_evidence_referenced") is True
    ),
    "drift_inputs_referenced": (
        infra_drift.get("check") == "public_infra_state_drift"
        and infra_drift.get("decision", {}).get("event_type") == "infra.state_drift.detected"
        and contract.get("inputs", {}).get("validation_event") == "infra.private_state.validated"
        and contract.get("inputs", {}).get("drift_event") == "infra.state_drift.detected"
        and evidence_source.get("infra_state_drift")
        == "infra/opentofu/state/drift-summary.sanitized.json"
        and evidence_checks.get("drift_inputs_referenced") is True
    ),
    "drifted_components_carried_forward": (
        contract.get("inputs", {}).get("drifted_components") == expected_drifted_components
        and infra_drift.get("drift", {}).get("drifted_components") == expected_drifted_components
        and evidence.get("plan", {}).get("drifted_components") == expected_drifted_components
        and sorted(action_by_component) == sorted(expected_drifted_components)
        and evidence_checks.get("drifted_components_carried_forward") is True
    ),
    "source_contracts_referenced": (
        contract_sources == expected_sources
        and evidence_source.get("remediation_contract")
        == "infra/state-remediation/private-infra-remediation-plan.sanitized.json"
        and evidence_checks.get("source_contracts_referenced") is True
    ),
    "opentofu_contract_referenced": (
        opentofu_plan.get("check") == "public_opentofu_plan"
        and opentofu_plan.get("plan", {}).get("mode") == "plan_only"
        and opentofu_plan.get("plan", {}).get("destroy_count") == 0
        and evidence_checks.get("opentofu_contract_referenced") is True
    ),
    "runtime_rollout_referenced": (
        runtime_rollout.get("check") == "public_runtime_rollout_evidence"
        and runtime_rollout.get("checks", {}).get("staging_health_success") is True
        and runtime_rollout.get("checks", {}).get("observability_stage_recorded") is True
        and evidence_checks.get("runtime_rollout_referenced") is True
    ),
    "gitops_remediation_referenced": (
        gitops_remediation.get("check") == "public_gitops_drift_remediation"
        and gitops_remediation.get("checks", {}).get("production_requires_approval") is True
        and gitops_remediation.get("checks", {}).get("plan_only_no_cluster_mutation") is True
        and evidence_checks.get("gitops_remediation_referenced") is True
    ),
    "preflight_gates_recorded": (
        all(action.get("preflight_gates") for action in actions)
        and "prometheus_targets" in action_by_component.get("observability", {}).get("preflight_gates", [])
        and "backup_restore_drill" in action_by_component.get("backup_storage", {}).get("preflight_gates", [])
        and staging_evidence.get("checks", {}).get("prometheus_required_targets_up") is True
        and evidence_checks.get("preflight_gates_recorded") is True
    ),
    "postcheck_gates_recorded": (
        all(action.get("postcheck_gates") for action in actions)
        and "sanitized_evidence_refresh" in action_by_component.get("observability", {}).get("postcheck_gates", [])
        and "restore_drill" in action_by_component.get("backup_storage", {}).get("postcheck_gates", [])
        and evidence_checks.get("postcheck_gates_recorded") is True
    ),
    "rollback_attached": (
        action_by_component.get("observability", {}).get("rollback") == "restore_previous_observability_config"
        and action_by_component.get("backup_storage", {}).get("rollback") == "keep_previous_backup_storage_target"
        and evidence_checks.get("rollback_attached") is True
    ),
    "operator_review_required": (
        contract.get("remediation_plan", {}).get("approval_required") is True
        and contract.get("decision", {}).get("operator_review_required") is True
        and evidence.get("decision", {}).get("operator_review_required") is True
        and evidence_checks.get("operator_review_required") is True
    ),
    "plan_only_no_apply": (
        planner.get("mode") == "plan_only"
        and planner.get("applies_infrastructure") is False
        and contract.get("remediation_plan", {}).get("automatic_apply") is False
        and evidence.get("plan", {}).get("mode") == "plan_only"
        and evidence.get("plan", {}).get("automatic_apply") is False
        and evidence.get("decision", {}).get("automatic_public_apply") is False
        and evidence_checks.get("plan_only_no_apply") is True
    ),
    "no_runtime_mutation_recorded": (
        planner.get("mutates_runtime") is False
        and planner.get("restarts_services") is False
        and boundaries.get("no_public_apply") is True
        and boundaries.get("no_cluster_mutation") is True
        and boundaries.get("no_service_restart") is True
        and evidence_checks.get("no_runtime_mutation_recorded") is True
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
    "private_markers_absent": (
        not any(marker in all_text for marker in private_markers)
        and evidence_checks.get("private_markers_absent") is True
    ),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_private_infra_remediation_plan",
    "data_profile": "sanitized_private_staging_summary",
    "remediation_model": "private_control_plane_remediation_plan",
    "source": {
        "remediation_contract": "infra/state-remediation/private-infra-remediation-plan.sanitized.json",
        "validation_contract": "infra/state-validation/private-infra-validation.sanitized.json",
        "validation_evidence": "docs/public/evidence/private-infra-validation.sanitized.json",
        "infra_state_drift": "infra/opentofu/state/drift-summary.sanitized.json",
        "opentofu_plan": "infra/opentofu/public/plan-summary.sanitized.json",
        "runtime_rollout": "docs/public/evidence/runtime-rollout.sanitized.json",
        "gitops_remediation": "docs/public/evidence/gitops-drift-remediation.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "plan": evidence.get("plan", {}),
    "checks": checks,
    "decision": {
        "event_type": "infra.remediation.plan.ready",
        "recommended_action": "review_plan_before_private_apply",
        "operator_review_required": True,
        "automatic_public_apply": False,
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
        print(f"missing public private infra remediation files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public private infra remediation check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print("public private infra remediation check ok: plan=private-infra-remediation-2026-06-18 mode=plan_only event=infra.remediation.plan.ready")
PY
