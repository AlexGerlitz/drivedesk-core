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

refresh_contract_path = remediation_dir / "private-infra-post-remediation-drift-refresh.sanitized.json"
refresh_evidence_path = public_docs / "evidence/private-infra-post-remediation-drift-refresh.sanitized.json"
execution_contract_path = remediation_dir / "private-infra-remediation-execution.sanitized.json"
execution_evidence_path = public_docs / "evidence/private-infra-remediation-execution.sanitized.json"
plan_contract_path = remediation_dir / "private-infra-remediation-plan.sanitized.json"
validation_contract_path = root / "infra/state-validation/private-infra-validation.sanitized.json"
validation_evidence_path = public_docs / "evidence/private-infra-validation.sanitized.json"
drift_summary_path = root / "infra/opentofu/state/drift-summary.sanitized.json"
desired_state_path = root / "infra/opentofu/state/desired-state.sanitized.json"
observed_state_path = root / "infra/opentofu/state/observed-state.sanitized.json"
opentofu_plan_path = root / "infra/opentofu/public/plan-summary.sanitized.json"
runtime_rollout_path = public_docs / "evidence/runtime-rollout.sanitized.json"
staging_evidence_path = public_docs / "evidence/de-staging-evidence.sanitized.json"
backup_restore_path = public_docs / "evidence/backup-restore-drill.sanitized.json"

required_files = [
    refresh_contract_path,
    refresh_evidence_path,
    execution_contract_path,
    execution_evidence_path,
    plan_contract_path,
    validation_contract_path,
    validation_evidence_path,
    drift_summary_path,
    desired_state_path,
    observed_state_path,
    opentofu_plan_path,
    runtime_rollout_path,
    staging_evidence_path,
    backup_restore_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": refresh_contract_path,
    "evidence": refresh_evidence_path,
    "execution_contract": execution_contract_path,
    "execution_evidence": execution_evidence_path,
    "plan_contract": plan_contract_path,
    "validation_contract": validation_contract_path,
    "validation_evidence": validation_evidence_path,
    "drift_summary": drift_summary_path,
    "desired_state": desired_state_path,
    "observed_state": observed_state_path,
    "opentofu_plan": opentofu_plan_path,
    "runtime_rollout": runtime_rollout_path,
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
execution_contract = payloads.get("execution_contract", {})
execution_evidence = payloads.get("execution_evidence", {})
plan_contract = payloads.get("plan_contract", {})
validation_contract = payloads.get("validation_contract", {})
validation_evidence = payloads.get("validation_evidence", {})
drift_summary = payloads.get("drift_summary", {})
desired_state = payloads.get("desired_state", {})
observed_state = payloads.get("observed_state", {})
opentofu_plan = payloads.get("opentofu_plan", {})
runtime_rollout = payloads.get("runtime_rollout", {})
staging_evidence = payloads.get("staging_evidence", {})
backup_restore = payloads.get("backup_restore", {})

expected_components = ["observability", "backup_storage"]
expected_sources = {
    "infra/state-remediation/private-infra-remediation-execution.sanitized.json",
    "docs/public/evidence/private-infra-remediation-execution.sanitized.json",
    "infra/state-remediation/private-infra-remediation-plan.sanitized.json",
    "docs/public/evidence/private-infra-remediation-plan.sanitized.json",
    "infra/state-validation/private-infra-validation.sanitized.json",
    "docs/public/evidence/private-infra-validation.sanitized.json",
    "infra/opentofu/state/drift-summary.sanitized.json",
    "infra/opentofu/state/desired-state.sanitized.json",
    "infra/opentofu/state/observed-state.sanitized.json",
    "infra/opentofu/public/plan-summary.sanitized.json",
    "docs/public/evidence/runtime-rollout.sanitized.json",
    "docs/public/evidence/de-staging-evidence.sanitized.json",
    "docs/public/evidence/backup-restore-drill.sanitized.json",
}
source = evidence.get("source", {})
refresh = contract.get("refresh", {})
evidence_refresh = evidence.get("refresh", {})
post_refresh_drift = contract.get("post_refresh_drift", {})
evidence_post_refresh_drift = evidence.get("post_refresh_drift", {})
boundaries = contract.get("boundaries", {})
checks = evidence.get("checks", {})
compared_components = refresh.get("compared_components", [])
compared_by_component = {component.get("component"): component for component in compared_components}

result_checks = {
    "refresh_files_present": not missing,
    "refresh_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("refresh_model") == "post_remediation_private_infra_drift_refresh"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
        and set(contract.get("source_contracts", [])) == expected_sources
        and evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_post_remediation_drift_refresh"
        and evidence.get("refresh_model") == "post_remediation_private_infra_drift_refresh"
        and checks.get("refresh_contract_present") is True
    ),
    "remediation_execution_referenced": (
        execution_contract.get("execution", {}).get("execution_id")
        == "private-infra-remediation-execution-2026-06-18"
        and execution_evidence.get("check") == "public_private_infra_remediation_execution"
        and execution_evidence.get("decision", {}).get("event_type")
        == "infra.remediation.execution.completed"
        and refresh.get("execution_id") == "private-infra-remediation-execution-2026-06-18"
        and refresh.get("triggered_by_event") == "infra.remediation.execution.completed"
        and source.get("remediation_execution")
        == "infra/state-remediation/private-infra-remediation-execution.sanitized.json"
        and source.get("remediation_execution_evidence")
        == "docs/public/evidence/private-infra-remediation-execution.sanitized.json"
        and checks.get("remediation_execution_referenced") is True
    ),
    "previous_drift_recorded": (
        drift_summary.get("drift", {}).get("detected") is True
        and drift_summary.get("drift", {}).get("drifted_components") == expected_components
        and plan_contract.get("inputs", {}).get("drifted_components") == expected_components
        and post_refresh_drift.get("previous_drifted_components") == expected_components
        and evidence_post_refresh_drift.get("previous_drifted_components") == expected_components
        and checks.get("previous_drift_recorded") is True
    ),
    "resolved_components_recorded": (
        post_refresh_drift.get("event_type") == "infra.post_remediation_drift.refreshed"
        and post_refresh_drift.get("resolved_components") == expected_components
        and evidence_post_refresh_drift.get("resolved_components") == expected_components
        and evidence_refresh.get("components") == expected_components
        and sorted(compared_by_component) == sorted(expected_components)
        and all(
            compared_by_component[component].get("refreshed_status") == "aligned"
            for component in expected_components
        )
        and checks.get("resolved_components_recorded") is True
    ),
    "no_residual_drift_recorded": (
        post_refresh_drift.get("residual_drift_components") == []
        and post_refresh_drift.get("accepted_drift_components") == []
        and evidence_post_refresh_drift.get("residual_drift_components") == []
        and evidence_post_refresh_drift.get("accepted_drift_components") == []
        and evidence_refresh.get("residual_drift_count") == 0
        and evidence_refresh.get("accepted_drift_count") == 0
        and all(
            compared_by_component[component].get("residual_drift") is False
            and compared_by_component[component].get("accepted_exception") is False
            for component in expected_components
        )
        and checks.get("no_residual_drift_recorded") is True
    ),
    "read_only_refresh_recorded": (
        refresh.get("refresh_id") == "private-infra-post-remediation-drift-refresh-2026-06-18"
        and refresh.get("mode") == "read_only_post_remediation_drift_refresh"
        and refresh.get("read_only") is True
        and refresh.get("automatic_apply") is False
        and refresh.get("public_apply") is False
        and refresh.get("production_apply") is False
        and evidence_refresh.get("read_only") is True
        and evidence_refresh.get("mode") == "read_only_post_remediation_drift_refresh"
        and checks.get("read_only_refresh_recorded") is True
    ),
    "state_sources_compared": (
        desired_state.get("state_model") == "public_opentofu_desired_state"
        and observed_state.get("state_model") == "public_opentofu_observed_state"
        and opentofu_plan.get("check") == "public_opentofu_plan"
        and post_refresh_drift.get("desired_state_compared") is True
        and post_refresh_drift.get("observed_state_compared") is True
        and post_refresh_drift.get("opentofu_plan_rechecked") is True
        and source.get("desired_state") == "infra/opentofu/state/desired-state.sanitized.json"
        and source.get("observed_state") == "infra/opentofu/state/observed-state.sanitized.json"
        and checks.get("state_sources_compared") is True
    ),
    "health_sources_rechecked": (
        validation_contract.get("validation_model") == "private_control_plane_state_validation"
        and validation_evidence.get("check") == "public_private_infra_validation"
        and runtime_rollout.get("check") == "public_runtime_rollout_evidence"
        and staging_evidence.get("checks", {}).get("prometheus_required_targets_up") is True
        and backup_restore.get("checks", {}).get("restore_integrity_ok") is True
        and "observability_evidence_refreshed" in refresh.get("gates_passed", [])
        and "backup_restore_evidence_refreshed" in refresh.get("gates_passed", [])
        and evidence_post_refresh_drift.get("runtime_evidence_rechecked") is True
        and checks.get("health_sources_rechecked") is True
    ),
    "no_apply_no_mutation": (
        boundaries.get("no_public_apply") is True
        and boundaries.get("no_production_apply") is True
        and boundaries.get("no_opentofu_apply") is True
        and boundaries.get("no_gitops_sync") is True
        and boundaries.get("no_runtime_mutation") is True
        and boundaries.get("no_service_restart") is True
        and evidence.get("decision", {}).get("automatic_public_apply") is False
        and evidence.get("decision", {}).get("production_data_touched") is False
        and checks.get("no_apply_no_mutation") is True
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
    "check": "public_private_infra_post_remediation_drift_refresh",
    "data_profile": "sanitized_private_staging_summary",
    "refresh_model": "post_remediation_private_infra_drift_refresh",
    "source": {
        "refresh_contract": "infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json",
        "remediation_execution": "infra/state-remediation/private-infra-remediation-execution.sanitized.json",
        "remediation_execution_evidence": "docs/public/evidence/private-infra-remediation-execution.sanitized.json",
        "remediation_plan": "infra/state-remediation/private-infra-remediation-plan.sanitized.json",
        "validation_contract": "infra/state-validation/private-infra-validation.sanitized.json",
        "validation_evidence": "docs/public/evidence/private-infra-validation.sanitized.json",
        "infra_state_drift": "infra/opentofu/state/drift-summary.sanitized.json",
        "desired_state": "infra/opentofu/state/desired-state.sanitized.json",
        "observed_state": "infra/opentofu/state/observed-state.sanitized.json",
        "opentofu_plan": "infra/opentofu/public/plan-summary.sanitized.json",
        "runtime_rollout": "docs/public/evidence/runtime-rollout.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
        "backup_restore": "docs/public/evidence/backup-restore-drill.sanitized.json",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "refresh": {
        "refresh_id": "private-infra-post-remediation-drift-refresh-2026-06-18",
        "execution_id": "private-infra-remediation-execution-2026-06-18",
        "triggered_by_event": "infra.remediation.execution.completed",
        "mode": "read_only_post_remediation_drift_refresh",
        "read_only": True,
        "components": expected_components,
        "residual_drift_count": 0,
        "accepted_drift_count": 0,
    },
    "post_refresh_drift": {
        "event_type": "infra.post_remediation_drift.refreshed",
        "previous_drifted_components": expected_components,
        "resolved_components": expected_components,
        "residual_drift_components": [],
        "accepted_drift_components": [],
        "desired_state_compared": True,
        "observed_state_compared": True,
        "runtime_evidence_rechecked": True,
    },
    "checks": result_checks,
    "decision": {
        "event_type": "infra.post_remediation_drift.clean",
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
    raise SystemExit("public private infra post-remediation drift refresh check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public private infra post-remediation drift refresh check ok: "
    "refresh=private-infra-post-remediation-drift-refresh-2026-06-18 "
    "event=infra.post_remediation_drift.clean"
)
PY
