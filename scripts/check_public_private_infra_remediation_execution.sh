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

execution_contract_path = remediation_dir / "private-infra-remediation-execution.sanitized.json"
execution_evidence_path = public_docs / "evidence/private-infra-remediation-execution.sanitized.json"
plan_contract_path = remediation_dir / "private-infra-remediation-plan.sanitized.json"
plan_evidence_path = public_docs / "evidence/private-infra-remediation-plan.sanitized.json"
validation_contract_path = root / "infra/state-validation/private-infra-validation.sanitized.json"
validation_evidence_path = public_docs / "evidence/private-infra-validation.sanitized.json"
infra_drift_path = root / "infra/opentofu/state/drift-summary.sanitized.json"
opentofu_plan_path = root / "infra/opentofu/public/plan-summary.sanitized.json"
runtime_rollout_path = public_docs / "evidence/runtime-rollout.sanitized.json"
gitops_remediation_path = public_docs / "evidence/gitops-drift-remediation.sanitized.json"
staging_evidence_path = public_docs / "evidence/de-staging-evidence.sanitized.json"
backup_restore_path = public_docs / "evidence/backup-restore-drill.sanitized.json"

required_files = [
    execution_contract_path,
    execution_evidence_path,
    plan_contract_path,
    plan_evidence_path,
    validation_contract_path,
    validation_evidence_path,
    infra_drift_path,
    opentofu_plan_path,
    runtime_rollout_path,
    gitops_remediation_path,
    staging_evidence_path,
    backup_restore_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": execution_contract_path,
    "evidence": execution_evidence_path,
    "plan_contract": plan_contract_path,
    "plan_evidence": plan_evidence_path,
    "validation_contract": validation_contract_path,
    "validation_evidence": validation_evidence_path,
    "infra_drift": infra_drift_path,
    "opentofu_plan": opentofu_plan_path,
    "runtime_rollout": runtime_rollout_path,
    "gitops_remediation": gitops_remediation_path,
    "staging_evidence": staging_evidence_path,
    "backup_restore": backup_restore_path,
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
plan_contract = payloads.get("plan_contract", {})
plan_evidence = payloads.get("plan_evidence", {})
validation_contract = payloads.get("validation_contract", {})
validation_evidence = payloads.get("validation_evidence", {})
infra_drift = payloads.get("infra_drift", {})
opentofu_plan = payloads.get("opentofu_plan", {})
runtime_rollout = payloads.get("runtime_rollout", {})
gitops_remediation = payloads.get("gitops_remediation", {})
staging_evidence = payloads.get("staging_evidence", {})
backup_restore = payloads.get("backup_restore", {})

expected_sources = {
    "infra/state-remediation/private-infra-remediation-plan.sanitized.json",
    "docs/public/evidence/private-infra-remediation-plan.sanitized.json",
    "infra/state-validation/private-infra-validation.sanitized.json",
    "docs/public/evidence/private-infra-validation.sanitized.json",
    "infra/opentofu/state/drift-summary.sanitized.json",
    "infra/opentofu/public/plan-summary.sanitized.json",
    "infra/runtime-rollout/private-staging-rollout.sanitized.json",
    "docs/public/evidence/runtime-rollout.sanitized.json",
    "docs/public/evidence/gitops-drift-remediation.sanitized.json",
    "docs/public/evidence/de-staging-evidence.sanitized.json",
    "docs/public/evidence/backup-restore-drill.sanitized.json",
}

expected_components = ["observability", "backup_storage"]
contract_sources = set(contract.get("source_contracts", []))
evidence_source = evidence.get("source", {})
contract_actions = contract.get("execution", {}).get("actions", [])
evidence_actions = evidence.get("execution", {}).get("actions", [])
contract_action_by_component = {action.get("component"): action for action in contract_actions}
evidence_action_by_component = {action.get("component"): action for action in evidence_actions}
approval = contract.get("approval", {})
evidence_approval = evidence.get("approval", {})
post_validation = contract.get("post_remediation_validation", {})
evidence_post_validation = evidence.get("post_remediation_validation", {})
boundaries = contract.get("boundaries", {})
checks = evidence.get("checks", {})

result_checks = {
    "execution_files_present": not missing,
    "execution_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("execution_model") == "reviewed_private_control_plane_remediation_execution"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
        and evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_remediation_execution"
        and evidence.get("execution_model") == "reviewed_private_control_plane_remediation_execution"
        and checks.get("execution_contract_present") is True
    ),
    "remediation_plan_referenced": (
        plan_contract.get("remediation_model") == "private_control_plane_remediation_plan"
        and plan_evidence.get("check") == "public_private_infra_remediation_plan"
        and plan_evidence.get("decision", {}).get("event_type") == "infra.remediation.plan.ready"
        and evidence_source.get("remediation_plan")
        == "infra/state-remediation/private-infra-remediation-plan.sanitized.json"
        and evidence_source.get("remediation_plan_evidence")
        == "docs/public/evidence/private-infra-remediation-plan.sanitized.json"
        and checks.get("remediation_plan_referenced") is True
    ),
    "source_contracts_referenced": (
        contract_sources == expected_sources
        and evidence_source.get("execution_contract")
        == "infra/state-remediation/private-infra-remediation-execution.sanitized.json"
        and evidence_source.get("validation_contract")
        == "infra/state-validation/private-infra-validation.sanitized.json"
        and evidence_source.get("validation_evidence")
        == "docs/public/evidence/private-infra-validation.sanitized.json"
    ),
    "operator_review_recorded": (
        approval.get("review_id") == "private-remediation-review-2026-06-18"
        and approval.get("plan_id") == "private-infra-remediation-2026-06-18"
        and approval.get("event_type") == "infra.remediation.execution.approved"
        and approval.get("approval_recorded") is True
        and approval.get("automatic_approval") is False
        and evidence_approval == approval
        and checks.get("operator_review_recorded") is True
    ),
    "reviewed_execution_recorded": (
        contract.get("execution", {}).get("execution_id")
        == "private-infra-remediation-execution-2026-06-18"
        and contract.get("execution", {}).get("mode") == "reviewed_private_staging_execution_summary"
        and contract.get("execution", {}).get("started_after_review") is True
        and contract.get("execution", {}).get("automatic_apply") is False
        and contract.get("execution", {}).get("public_apply") is False
        and contract.get("execution", {}).get("production_apply") is False
        and evidence.get("execution", {}).get("mode") == "reviewed_private_staging_execution_summary"
        and checks.get("reviewed_execution_recorded") is True
    ),
    "drifted_components_executed": (
        infra_drift.get("drift", {}).get("drifted_components") == expected_components
        and plan_evidence.get("plan", {}).get("drifted_components") == expected_components
        and evidence.get("execution", {}).get("components") == expected_components
        and sorted(contract_action_by_component) == sorted(expected_components)
        and sorted(evidence_action_by_component) == sorted(expected_components)
        and all(
            action.get("execution_status") == "completed"
            for action in contract_actions
        )
        and all(
            action.get("status") == "completed"
            for action in evidence_actions
        )
        and checks.get("drifted_components_executed") is True
    ),
    "preflight_gates_passed": (
        validation_contract.get("validation_model") == "private_control_plane_state_validation"
        and validation_evidence.get("check") == "public_private_infra_validation"
        and all(action.get("preflight_gates_passed") for action in contract_actions)
        and "prometheus_targets" in contract_action_by_component.get("observability", {}).get("preflight_gates_passed", [])
        and "backup_restore_drill" in contract_action_by_component.get("backup_storage", {}).get("preflight_gates_passed", [])
        and staging_evidence.get("checks", {}).get("prometheus_required_targets_up") is True
        and backup_restore.get("checks", {}).get("restore_integrity_ok") is True
        and checks.get("preflight_gates_passed") is True
    ),
    "postcheck_gates_passed": (
        runtime_rollout.get("check") == "public_runtime_rollout_evidence"
        and runtime_rollout.get("checks", {}).get("staging_health_success") is True
        and all(action.get("postcheck_gates_passed") for action in contract_actions)
        and "observability_evidence" in contract_action_by_component.get("observability", {}).get("postcheck_gates_passed", [])
        and "restore_drill" in contract_action_by_component.get("backup_storage", {}).get("postcheck_gates_passed", [])
        and checks.get("postcheck_gates_passed") is True
    ),
    "rollback_available_not_used": (
        contract_action_by_component.get("observability", {}).get("rollback") == "restore_previous_observability_config"
        and contract_action_by_component.get("backup_storage", {}).get("rollback") == "keep_previous_backup_storage_target"
        and all(action.get("rollback_executed") is False for action in contract_actions)
        and all(action.get("rollback_executed") is False for action in evidence_actions)
        and checks.get("rollback_available_not_used") is True
    ),
    "post_remediation_validation_recorded": (
        post_validation.get("event_type") == "infra.remediation.execution.validated"
        and post_validation.get("drift_resolved_components") == expected_components
        and post_validation.get("private_validation_refreshed") is True
        and post_validation.get("runtime_health_refreshed") is True
        and post_validation.get("observability_evidence_refreshed") is True
        and post_validation.get("backup_restore_evidence_refreshed") is True
        and evidence_post_validation.get("event_type") == "infra.remediation.execution.validated"
        and evidence_post_validation.get("drift_resolved_components") == expected_components
        and checks.get("post_remediation_validation_recorded") is True
    ),
    "sanitized_evidence_refreshed": (
        post_validation.get("sanitized_evidence_refreshed") is True
        and evidence_post_validation.get("sanitized_evidence_refreshed") is True
        and checks.get("sanitized_evidence_refreshed") is True
    ),
    "no_public_apply": (
        boundaries.get("no_public_apply") is True
        and boundaries.get("no_public_cluster_mutation") is True
        and evidence.get("decision", {}).get("automatic_public_apply") is False
        and checks.get("no_public_apply") is True
    ),
    "no_production_apply": (
        boundaries.get("no_production_apply") is True
        and contract.get("execution", {}).get("production_apply") is False
        and contract.get("execution", {}).get("production_data_touched") is False
        and checks.get("no_production_apply") is True
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
        and checks.get("redaction_boundary_recorded") is True
    ),
    "private_markers_absent": (
        not any(marker in all_text for marker in private_markers)
        and checks.get("private_markers_absent") is True
    ),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_private_infra_remediation_execution",
    "data_profile": "sanitized_private_staging_summary",
    "execution_model": "reviewed_private_control_plane_remediation_execution",
    "source": {
        "execution_contract": "infra/state-remediation/private-infra-remediation-execution.sanitized.json",
        "remediation_plan": "infra/state-remediation/private-infra-remediation-plan.sanitized.json",
        "remediation_plan_evidence": "docs/public/evidence/private-infra-remediation-plan.sanitized.json",
        "validation_contract": "infra/state-validation/private-infra-validation.sanitized.json",
        "validation_evidence": "docs/public/evidence/private-infra-validation.sanitized.json",
        "infra_state_drift": "infra/opentofu/state/drift-summary.sanitized.json",
        "opentofu_plan": "infra/opentofu/public/plan-summary.sanitized.json",
        "runtime_rollout": "docs/public/evidence/runtime-rollout.sanitized.json",
        "gitops_remediation": "docs/public/evidence/gitops-drift-remediation.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
        "backup_restore": "docs/public/evidence/backup-restore-drill.sanitized.json",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "approval": {
        "review_id": "private-remediation-review-2026-06-18",
        "plan_id": "private-infra-remediation-2026-06-18",
        "event_type": "infra.remediation.execution.approved",
        "reviewer_role": "operator",
        "approval_recorded": True,
        "automatic_approval": False,
        "public_apply": False,
    },
    "execution": {
        "execution_id": "private-infra-remediation-execution-2026-06-18",
        "mode": "reviewed_private_staging_execution_summary",
        "plan_id": "private-infra-remediation-2026-06-18",
        "components": expected_components,
        "actions": [
            {
                "component": "observability",
                "status": "completed",
                "approved_action": "reconcile_after_review",
                "rollback": "restore_previous_observability_config",
                "rollback_executed": False,
            },
            {
                "component": "backup_storage",
                "status": "completed",
                "approved_action": "reconcile_after_review",
                "rollback": "keep_previous_backup_storage_target",
                "rollback_executed": False,
            },
        ],
    },
    "post_remediation_validation": {
        "event_type": "infra.remediation.execution.validated",
        "drift_resolved_components": expected_components,
        "private_validation_refreshed": True,
        "runtime_health_refreshed": True,
        "sanitized_evidence_refreshed": True,
    },
    "checks": result_checks,
    "decision": {
        "event_type": "infra.remediation.execution.completed",
        "recommended_action": "continue_scheduled_validation",
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

passed = all(value for key, value in result_checks.items() if key != "production_data_touched")
passed = passed and result_checks["production_data_touched"] is False

if missing:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(f"missing required files: {missing}")
if not passed:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit("public private infra remediation execution check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public private infra remediation execution check ok: "
    "execution=private-infra-remediation-execution-2026-06-18 "
    "event=infra.remediation.execution.completed"
)
PY
