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

schedule_contract_path = validation_dir / "private-infra-scheduled-validation.sanitized.json"
schedule_evidence_path = public_docs / "evidence/private-infra-scheduled-validation.sanitized.json"
workflow_path = root / ".github/workflows/scheduled-validation.yml"
post_refresh_contract_path = (
    root / "infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json"
)
post_refresh_evidence_path = (
    public_docs / "evidence/private-infra-post-remediation-drift-refresh.sanitized.json"
)
execution_contract_path = root / "infra/state-remediation/private-infra-remediation-execution.sanitized.json"
execution_evidence_path = public_docs / "evidence/private-infra-remediation-execution.sanitized.json"
validation_contract_path = validation_dir / "private-infra-validation.sanitized.json"
validation_evidence_path = public_docs / "evidence/private-infra-validation.sanitized.json"
runtime_rollout_path = public_docs / "evidence/runtime-rollout.sanitized.json"
staging_evidence_path = public_docs / "evidence/de-staging-evidence.sanitized.json"

required_files = [
    schedule_contract_path,
    schedule_evidence_path,
    workflow_path,
    post_refresh_contract_path,
    post_refresh_evidence_path,
    execution_contract_path,
    execution_evidence_path,
    validation_contract_path,
    validation_evidence_path,
    runtime_rollout_path,
    staging_evidence_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": schedule_contract_path,
    "evidence": schedule_evidence_path,
    "post_refresh_contract": post_refresh_contract_path,
    "post_refresh_evidence": post_refresh_evidence_path,
    "execution_contract": execution_contract_path,
    "execution_evidence": execution_evidence_path,
    "validation_contract": validation_contract_path,
    "validation_evidence": validation_evidence_path,
    "runtime_rollout": runtime_rollout_path,
    "staging_evidence": staging_evidence_path,
}.items():
    if path.is_file():
        payloads[key] = json.loads(path.read_text(encoding="utf-8"))

workflow_text = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
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
post_refresh_contract = payloads.get("post_refresh_contract", {})
post_refresh_evidence = payloads.get("post_refresh_evidence", {})
execution_contract = payloads.get("execution_contract", {})
execution_evidence = payloads.get("execution_evidence", {})
validation_contract = payloads.get("validation_contract", {})
validation_evidence = payloads.get("validation_evidence", {})
runtime_rollout = payloads.get("runtime_rollout", {})
staging_evidence = payloads.get("staging_evidence", {})

expected_sources = {
    "infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json",
    "docs/public/evidence/private-infra-post-remediation-drift-refresh.sanitized.json",
    "infra/state-remediation/private-infra-remediation-execution.sanitized.json",
    "docs/public/evidence/private-infra-remediation-execution.sanitized.json",
    "infra/state-validation/private-infra-validation.sanitized.json",
    "docs/public/evidence/private-infra-validation.sanitized.json",
    "docs/public/evidence/runtime-rollout.sanitized.json",
    "docs/public/evidence/de-staging-evidence.sanitized.json",
    ".github/workflows/scheduled-validation.yml",
}

source = evidence.get("source", {})
scheduler = contract.get("scheduler", {})
evidence_scheduler = evidence.get("scheduler", {})
runs = contract.get("scheduled_runs", [])
run_summary = evidence.get("run_summary", {})
missed_run_guard = contract.get("missed_run_guard", {})
boundaries = contract.get("boundaries", {})
checks = evidence.get("checks", {})

result_checks = {
    "scheduled_validation_files_present": not missing,
    "schedule_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("schedule_model") == "recurring_private_infra_validation"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
        and set(contract.get("source_contracts", [])) == expected_sources
        and evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_scheduled_validation"
        and evidence.get("schedule_model") == "recurring_private_infra_validation"
        and source.get("schedule_contract")
        == "infra/state-validation/private-infra-scheduled-validation.sanitized.json"
        and checks.get("schedule_contract_present") is True
    ),
    "workflow_schedule_present": (
        "name: Public Scheduled Validation" in workflow_text
        and "workflow_dispatch:" in workflow_text
        and "schedule:" in workflow_text
        and 'cron: "23 4 * * *"' in workflow_text
        and "permissions:" in workflow_text
        and "contents: read" in workflow_text
        and source.get("workflow") == ".github/workflows/scheduled-validation.yml"
        and scheduler.get("workflow_path") == ".github/workflows/scheduled-validation.yml"
        and evidence_scheduler.get("workflow_path") == ".github/workflows/scheduled-validation.yml"
        and checks.get("workflow_schedule_present") is True
    ),
    "workflow_dispatch_present": (
        "workflow_dispatch:" in workflow_text
        and "workflow_dispatch" in scheduler.get("trigger_modes", [])
        and "workflow_dispatch" in evidence_scheduler.get("trigger_modes", [])
        and checks.get("workflow_dispatch_present") is True
    ),
    "scheduled_checker_runs": (
        "bash scripts/check_public_private_infra_scheduled_validation.sh" in workflow_text
        and checks.get("scheduled_checker_runs") is True
    ),
    "post_remediation_refresh_rechecked": (
        "bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh" in workflow_text
        and post_refresh_contract.get("refresh_model") == "post_remediation_private_infra_drift_refresh"
        and post_refresh_evidence.get("check") == "public_private_infra_post_remediation_drift_refresh"
        and post_refresh_evidence.get("decision", {}).get("event_type")
        == "infra.post_remediation_drift.clean"
        and source.get("post_remediation_drift_refresh")
        == "infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json"
        and checks.get("post_remediation_refresh_rechecked") is True
    ),
    "secret_boundary_rechecked": (
        "bash scripts/check_public_export_secrets.sh" in workflow_text
        and "bash scripts/check_secrets.sh" in workflow_text
        and checks.get("secret_boundary_rechecked") is True
    ),
    "sample_runs_recorded": (
        len(runs) == 3
        and all(run.get("status") == "passed" for run in runs)
        and all(run.get("drift_status") == "clean" for run in runs)
        and all(run.get("production_data_touched") is False for run in runs)
        and run_summary.get("sampled_runs") == 3
        and run_summary.get("successful_runs") == 3
        and run_summary.get("failed_runs") == 0
        and run_summary.get("drift_status") == "clean"
        and checks.get("sample_runs_recorded") is True
    ),
    "missed_run_guard_recorded": (
        missed_run_guard.get("event_type") == "infra.scheduled_validation.missed"
        and missed_run_guard.get("latest_run_within_slo") is True
        and missed_run_guard.get("max_expected_interval_hours") == 26
        and missed_run_guard.get("consecutive_successful_runs") == 3
        and missed_run_guard.get("alert_route") == "operator_review"
        and missed_run_guard.get("requires_investigation_on_miss") is True
        and run_summary.get("latest_run_within_slo") is True
        and checks.get("missed_run_guard_recorded") is True
    ),
    "read_only_schedule_recorded": (
        scheduler.get("schedule_id") == "private-infra-scheduled-validation-2026-06-18"
        and scheduler.get("workflow_name") == "Public Scheduled Validation"
        and scheduler.get("cron_utc") == "23 4 * * *"
        and scheduler.get("cadence") == "daily"
        and scheduler.get("read_only") is True
        and scheduler.get("automatic_apply") is False
        and scheduler.get("public_apply") is False
        and scheduler.get("production_apply") is False
        and evidence_scheduler.get("read_only") is True
        and evidence_scheduler.get("cron_utc") == "23 4 * * *"
        and checks.get("read_only_schedule_recorded") is True
    ),
    "source_contracts_referenced": (
        validation_contract.get("validation_model") == "private_control_plane_state_validation"
        and validation_evidence.get("check") == "public_private_infra_validation"
        and execution_contract.get("execution", {}).get("execution_id")
        == "private-infra-remediation-execution-2026-06-18"
        and execution_evidence.get("decision", {}).get("event_type")
        == "infra.remediation.execution.completed"
        and runtime_rollout.get("check") == "public_runtime_rollout_evidence"
        and staging_evidence.get("checks", {}).get("prometheus_required_targets_up") is True
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
    "check": "public_private_infra_scheduled_validation",
    "data_profile": "sanitized_private_staging_summary",
    "schedule_model": "recurring_private_infra_validation",
    "source": {
        "schedule_contract": "infra/state-validation/private-infra-scheduled-validation.sanitized.json",
        "workflow": ".github/workflows/scheduled-validation.yml",
        "post_remediation_drift_refresh": (
            "infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json"
        ),
        "post_remediation_drift_refresh_evidence": (
            "docs/public/evidence/private-infra-post-remediation-drift-refresh.sanitized.json"
        ),
        "remediation_execution": "infra/state-remediation/private-infra-remediation-execution.sanitized.json",
        "remediation_execution_evidence": "docs/public/evidence/private-infra-remediation-execution.sanitized.json",
        "validation_contract": "infra/state-validation/private-infra-validation.sanitized.json",
        "validation_evidence": "docs/public/evidence/private-infra-validation.sanitized.json",
        "runtime_rollout": "docs/public/evidence/runtime-rollout.sanitized.json",
        "staging_evidence": "docs/public/evidence/de-staging-evidence.sanitized.json",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "scheduler": {
        "schedule_id": "private-infra-scheduled-validation-2026-06-18",
        "workflow_name": "Public Scheduled Validation",
        "workflow_path": ".github/workflows/scheduled-validation.yml",
        "cron_utc": "23 4 * * *",
        "cadence": "daily",
        "trigger_modes": ["schedule", "workflow_dispatch"],
        "read_only": True,
        "timeout_minutes": 12,
    },
    "run_summary": {
        "sampled_runs": 3,
        "successful_runs": 3,
        "failed_runs": 0,
        "latest_run_within_slo": True,
        "consecutive_successful_runs": 3,
        "drift_status": "clean",
    },
    "checks": result_checks,
    "decision": {
        "event_type": "infra.scheduled_validation.healthy",
        "recommended_action": "continue_recurring_validation",
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
    raise SystemExit("public private infra scheduled validation check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public private infra scheduled validation check ok: "
    "schedule=private-infra-scheduled-validation-2026-06-18 "
    "event=infra.scheduled_validation.healthy"
)
PY
