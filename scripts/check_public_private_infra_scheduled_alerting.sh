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

alert_contract_path = validation_dir / "private-infra-scheduled-alerting.sanitized.json"
alert_evidence_path = public_docs / "evidence/private-infra-scheduled-alerting.sanitized.json"
scheduled_contract_path = validation_dir / "private-infra-scheduled-validation.sanitized.json"
scheduled_evidence_path = public_docs / "evidence/private-infra-scheduled-validation.sanitized.json"
workflow_path = root / ".github/workflows/scheduled-validation.yml"
public_doc_path = public_docs / "PRIVATE_INFRA_SCHEDULED_ALERTING.md"
adr_path = root / "docs/adr/0060-public-safe-private-infra-scheduled-alerting.md"

required_files = [
    alert_contract_path,
    alert_evidence_path,
    scheduled_contract_path,
    scheduled_evidence_path,
    workflow_path,
    public_doc_path,
    adr_path,
]
missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

payloads = {}
for key, path in {
    "contract": alert_contract_path,
    "evidence": alert_evidence_path,
    "scheduled_contract": scheduled_contract_path,
    "scheduled_evidence": scheduled_evidence_path,
}.items():
    if path.is_file():
        payloads[key] = json.loads(path.read_text(encoding="utf-8"))

workflow_text = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
public_doc_text = public_doc_path.read_text(encoding="utf-8") if public_doc_path.is_file() else ""
adr_text = adr_path.read_text(encoding="utf-8") if adr_path.is_file() else ""
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
scheduled_contract = payloads.get("scheduled_contract", {})
scheduled_evidence = payloads.get("scheduled_evidence", {})

alert_policy = contract.get("alert_policy", {})
evidence_policy = evidence.get("alert_policy", {})
workflow_handler = contract.get("workflow_failure_handler", {})
evidence_handler = evidence.get("workflow_failure_handler", {})
boundaries = contract.get("boundaries", {})
checks = evidence.get("checks", {})
signals = {signal.get("event_type"): signal for signal in alert_policy.get("signals", [])}
runbooks = {runbook.get("runbook_key"): runbook for runbook in contract.get("runbooks", [])}

expected_signals = {
    "infra.scheduled_validation.missed",
    "infra.scheduled_validation.failed",
    "infra.scheduled_validation.secret_boundary_failed",
}
expected_runbooks = {
    "scheduled_validation.missed",
    "scheduled_validation.failed",
    "scheduled_validation.secret_boundary_failed",
}
expected_sources = {
    "infra/state-validation/private-infra-scheduled-validation.sanitized.json",
    "docs/public/evidence/private-infra-scheduled-validation.sanitized.json",
    ".github/workflows/scheduled-validation.yml",
}

result_checks = {
    "scheduled_alerting_files_present": not missing,
    "alerting_contract_present": (
        contract.get("schema_version") == 1
        and contract.get("alerting_model") == "scheduled_validation_alerting"
        and contract.get("data_profile") == "sanitized_private_staging_summary"
        and set(contract.get("source_contracts", [])) == expected_sources
        and evidence.get("schema_version") == 1
        and evidence.get("check") == "public_private_infra_scheduled_alerting"
        and evidence.get("alerting_model") == "scheduled_validation_alerting"
        and evidence.get("source", {}).get("alerting_contract")
        == "infra/state-validation/private-infra-scheduled-alerting.sanitized.json"
        and checks.get("alerting_contract_present") is True
    ),
    "workflow_failure_handler_present": (
        "Emit scheduled validation alert payload" in workflow_text
        and "Upload scheduled validation alert payload" in workflow_text
        and "if: failure()" in workflow_text
        and "actions/upload-artifact@v4" in workflow_text
        and "public-scheduled-validation-alert" in workflow_text
        and ".scheduled-validation-alert/alert.json" in workflow_text
        and "infra.scheduled_validation.failed" in workflow_text
        and "scheduled_validation.failed" in workflow_text
        and workflow_handler.get("artifact_name") == "public-scheduled-validation-alert"
        and workflow_handler.get("emits_event_type") == "infra.scheduled_validation.failed"
        and evidence_handler.get("artifact_name") == "public-scheduled-validation-alert"
        and evidence_handler.get("runbook_key") == "scheduled_validation.failed"
        and checks.get("workflow_failure_handler_present") is True
    ),
    "missed_run_alert_recorded": (
        signals.get("infra.scheduled_validation.missed", {}).get("severity") == "warning"
        and signals.get("infra.scheduled_validation.missed", {}).get("runbook_key")
        == "scheduled_validation.missed"
        and signals.get("infra.scheduled_validation.missed", {}).get("notification_route")
        == "operator_review"
        and "latest_run_age_hours > 26"
        in signals.get("infra.scheduled_validation.missed", {}).get("condition", "")
        and checks.get("missed_run_alert_recorded") is True
    ),
    "failed_run_alert_recorded": (
        signals.get("infra.scheduled_validation.failed", {}).get("severity") == "critical"
        and signals.get("infra.scheduled_validation.failed", {}).get("runbook_key")
        == "scheduled_validation.failed"
        and signals.get("infra.scheduled_validation.failed", {}).get("notification_route")
        == "github_actions_failure_artifact"
        and checks.get("failed_run_alert_recorded") is True
    ),
    "secret_boundary_alert_recorded": (
        signals.get("infra.scheduled_validation.secret_boundary_failed", {}).get("severity")
        == "critical"
        and signals.get("infra.scheduled_validation.secret_boundary_failed", {}).get("runbook_key")
        == "scheduled_validation.secret_boundary_failed"
        and signals.get("infra.scheduled_validation.secret_boundary_failed", {}).get(
            "notification_route"
        )
        == "operator_review"
        and checks.get("secret_boundary_alert_recorded") is True
    ),
    "runbook_catalog_recorded": (
        set(runbooks) == expected_runbooks
        and all(runbook.get("first_actions") for runbook in runbooks.values())
        and runbooks["scheduled_validation.failed"].get("release_gate") == "block promotion"
        and checks.get("runbook_catalog_recorded") is True
    ),
    "notification_routes_recorded": (
        set(alert_policy.get("notification_channels", []))
        == {"github_actions_failure", "public_safe_failure_artifact", "operator_review"}
        and set(evidence_policy.get("notification_channels", []))
        == {"github_actions_failure", "public_safe_failure_artifact", "operator_review"}
        and set(evidence_policy.get("signals_recorded", [])) == expected_signals
        and alert_policy.get("external_notifications_enabled") is False
        and evidence_policy.get("external_notifications_enabled") is False
        and checks.get("notification_routes_recorded") is True
    ),
    "scheduled_validation_source_referenced": (
        scheduled_contract.get("schedule_model") == "recurring_private_infra_validation"
        and scheduled_evidence.get("check") == "public_private_infra_scheduled_validation"
        and scheduled_evidence.get("decision", {}).get("event_type")
        == "infra.scheduled_validation.healthy"
        and evidence.get("source", {}).get("scheduled_validation_contract")
        == "infra/state-validation/private-infra-scheduled-validation.sanitized.json"
        and checks.get("scheduled_validation_source_referenced") is True
    ),
    "no_external_secret_required": (
        alert_policy.get("requires_private_secrets") is False
        and evidence_policy.get("requires_private_secrets") is False
        and boundaries.get("no_external_notification_secret") is True
        and checks.get("no_external_secret_required") is True
    ),
    "docs_and_adr_reference_alerting": (
        "public-scheduled-validation-alert" in public_doc_text
        and "infra.scheduled_validation.secret_boundary_failed" in public_doc_text
        and "scheduled_validation_alerting" in adr_text
        and "scripts/check_public_private_infra_scheduled_alerting.sh" in adr_text
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
    ),
    "private_markers_absent": (
        not any(marker in all_text for marker in private_markers)
        and checks.get("private_markers_absent") is True
    ),
    "production_data_touched": False,
}

payload = {
    "schema_version": 1,
    "check": "public_private_infra_scheduled_alerting",
    "data_profile": "sanitized_private_staging_summary",
    "alerting_model": "scheduled_validation_alerting",
    "source": {
        "alerting_contract": "infra/state-validation/private-infra-scheduled-alerting.sanitized.json",
        "scheduled_validation_contract": (
            "infra/state-validation/private-infra-scheduled-validation.sanitized.json"
        ),
        "scheduled_validation_evidence": (
            "docs/public/evidence/private-infra-scheduled-validation.sanitized.json"
        ),
        "workflow": ".github/workflows/scheduled-validation.yml",
    },
    "environment": {
        "name": "private_staging",
        "public_route": False,
        "production_data_touched": False,
    },
    "alert_policy": {
        "policy_id": "private-infra-scheduled-alerting-2026-06-18",
        "deduplication_key": "private-infra-scheduled-validation",
        "signals_recorded": sorted(expected_signals),
        "notification_channels": [
            "github_actions_failure",
            "public_safe_failure_artifact",
            "operator_review",
        ],
        "external_notifications_enabled": False,
        "requires_private_secrets": False,
    },
    "workflow_failure_handler": {
        "artifact_name": "public-scheduled-validation-alert",
        "artifact_path": ".scheduled-validation-alert/alert.json",
        "emits_event_type": "infra.scheduled_validation.failed",
        "runbook_key": "scheduled_validation.failed",
        "read_only": True,
    },
    "checks": result_checks,
    "decision": {
        "event_type": "infra.scheduled_validation.alerting.ready",
        "recommended_action": "review failed or missed scheduled validation before release promotion",
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
    raise SystemExit("public private infra scheduled alerting check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public private infra scheduled alerting check ok: "
    "policy=private-infra-scheduled-alerting-2026-06-18 "
    "event=infra.scheduled_validation.alerting.ready"
)
PY
