#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

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

export PYTHONPATH="$ROOT/apps/api:$ROOT/apps/worker:$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

SERVER_PID=""
LOG_FILE=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$LOG_FILE" && -f "$LOG_FILE" ]]; then
    rm -f "$LOG_FILE"
  fi
}
trap cleanup EXIT

if [[ -n "${DRIVEDESK_DEMO_BASE_URL:-}" ]]; then
  BASE_URL="${DRIVEDESK_DEMO_BASE_URL%/}"
else
  PORT="${DRIVEDESK_DEMO_API_PORT:-}"
  if [[ -z "$PORT" ]]; then
    PORT="$("$PYTHON_BIN" - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
  fi
  BASE_URL="http://127.0.0.1:$PORT"
  LOG_FILE="$(mktemp -t drivedesk-public-demo-api.XXXXXX.log)"
  "$PYTHON_BIN" -m uvicorn drivedesk_api.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --log-level warning \
    >"$LOG_FILE" 2>&1 &
  SERVER_PID="$!"
fi

"$PYTHON_BIN" - <<'PY' "$BASE_URL" "$ROOT/docs/openapi.json"
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

base_url = sys.argv[1].rstrip("/")
openapi_file = Path(sys.argv[2])


def get_json(path: str) -> tuple[dict, dict[str, str]]:
    request = urllib.request.Request(f"{base_url}{path}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
        return payload, headers


def get_text(path: str) -> tuple[str, dict[str, str]]:
    request = urllib.request.Request(f"{base_url}{path}", headers={"Accept": "text/plain"})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = response.read().decode("utf-8")
        headers = {key.lower(): value for key, value in response.headers.items()}
        return payload, headers


deadline = time.monotonic() + 20
last_error: Exception | None = None
while time.monotonic() < deadline:
    try:
        health, _ = get_json("/health")
        if health.get("status") == "ok":
            break
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        last_error = exc
        time.sleep(0.5)
else:
    raise SystemExit(f"API did not become healthy: {last_error}")

health, _ = get_json("/health")
ready, _ = get_json("/ready")
demo, demo_headers = get_json("/demo/public")
adapters, _ = get_json("/integration-adapters")
runbooks, _ = get_json("/integration-runbooks")
lifecycle_policies, _ = get_json("/business-record-lifecycle-policies")
openapi, _ = get_json("/openapi.json")
metrics, metrics_headers = get_text("/metrics")

assert health["status"] == "ok", health
assert ready["status"] in {"ready", "degraded"}, ready
assert demo["schemaVersion"] == 1, demo
assert demo["dataSource"] == "api.synthetic", demo
assert demo["apiContract"]["path"] == "/demo/public", demo
assert demo["apiContract"]["data_profile"] == "synthetic_demo_data", demo
assert demo["tenant"]["slug"] == "demo-academy", demo
assert demo["workflow"]["id"] == "wf-demo-lead-to-student", demo
assert demo["workflow"]["currentStage"] == "student_sync", demo
assert len(demo["workflow"]["stages"]) >= 5, demo
assert {stage["state"] for stage in demo["workflow"]["stages"]} >= {"done", "current"}, demo
assert len(demo["workflowScenarios"]) >= 3, demo
scenario_by_id = {scenario["id"]: scenario for scenario in demo["workflowScenarios"]}
assert set(scenario_by_id) >= {
    "scenario-contract-approval-sync",
    "scenario-signature-task",
    "scenario-accounting-export",
}, demo
assert {scenario["actionType"] for scenario in demo["workflowScenarios"]} >= {
    "emit_outbox_event",
    "create_task_record",
    "request_adapter_sync",
}, demo
assert {
    output
    for scenario in demo["workflowScenarios"]
    for output in scenario["outputs"]
} >= {
    "audit_event",
    "outbox_event",
    "task_record",
    "integration_job",
    "action_run",
}, demo
assert scenario_by_id["scenario-contract-approval-sync"]["trigger"] == (
    "business_record.status_changed contract:draft->approved"
), demo
assert scenario_by_id["scenario-signature-task"]["evidence"] == "workflow.task_record.created", demo
assert scenario_by_id["scenario-accounting-export"]["status"] == "pending", demo
end_to_end = demo["endToEndScenario"]
assert end_to_end["id"] == "scenario-approval-notification-adapter-incident", demo
assert end_to_end["status"] == "reviewable", demo
assert end_to_end["currentStep"] == "incident_resolved", demo
assert len(end_to_end["chain"]) >= 6, demo
assert {step["step"] for step in end_to_end["chain"]} >= {
    "approval",
    "notification",
    "adapter",
    "incident",
    "recovery",
    "proof",
}, demo
assert {step["evidence"] for step in end_to_end["chain"]} >= {
    "workflow.contract_approved",
    "notification.manager_signature_task.created",
    "integration.accounting_export.requested",
    "integration.incident.status_changed",
    "postcheck.gates.passed",
    "docs/public/ENGINEERING_PROOF.md",
}, demo
assert set(end_to_end["proof"]) >= {
    "workflow.contract_approved",
    "notification.manager_signature_task.created",
    "integration.accounting_export.requested",
    "integration.incident.status_changed",
    "postcheck.gates.passed",
    "docs/public/ENGINEERING_PROOF.md",
}, demo
assert len(demo["timeline"]) >= 5, demo
assert len(demo["domainEvents"]) >= 4, demo
assert {event["event"] for event in demo["domainEvents"]} >= {
    "lead.created",
    "student.created",
    "contract.generated",
    "student.sync.requested",
}
assert len(demo["integrationHealth"]) >= 6, demo
assert len(demo["recoveryEvidence"]) >= 4, demo
assert {route["name"] for route in demo["alertRouting"]["routes"]} >= {
    "platform-critical-page",
    "platform-warning-ticket",
    "scheduled-validation-notice",
}, demo
assert {binding["alert"] for binding in demo["alertRouting"]["bindings"]} >= {
    "DriveDeskApiTargetDown",
    "DriveDeskIntegrationDeadLetters",
    "DriveDeskScheduledValidationMissed",
}, demo
assert {binding["state"] for binding in demo["alertRouting"]["bindings"]} == {"routed"}, demo
assert {action["evidence"] for action in demo["alertRouting"]["runbookActions"]} >= {
    "ALERT_ROUTING_EVIDENCE.md",
    "alert.silence.created",
}, demo
assert {incident["status"] for incident in demo["incidentResponse"]["incidents"]} >= {
    "open",
    "acknowledged",
    "resolved",
}, demo
assert {incident["alert"] for incident in demo["incidentResponse"]["incidents"]} >= {
    "DriveDeskApiHighLatencyP95",
    "DriveDeskIntegrationDeadLetters",
    "DriveDeskScheduledValidationMissed",
}, demo
assert {event["event"] for event in demo["incidentResponse"]["timeline"]} >= {
    "alert.fired",
    "integration.incident.status_changed",
    "incident.resolved",
}, demo
assert {action["evidence"] for action in demo["incidentResponse"]["recoveryActions"]} >= {
    "outbox.retry.requested",
    "postcheck.gates.passed",
    "incident.resolved",
}, demo
assert {item["evidence"] for item in demo["incidentResponse"]["resolutionEvidence"]} >= {
    "drivedesk_integration_incidents",
    "INTEGRATION_INCIDENT_RUNBOOKS.md",
    "postcheck.gates.passed",
}, demo
control_tower = demo["businessControlTower"]
assert {item["label"] for item in control_tower["summary"]} >= {
    "Observed systems",
    "Open exceptions",
    "Repair actions",
    "External writes",
}, demo
assert control_tower["detection"]["ruleSet"] == "payment_reconciliation", demo
assert control_tower["detection"]["status"] == "detected", demo
assert {item["type"] for item in control_tower["detection"]["detectedExceptions"]} == {
    "crm_payment_mismatch"
}, demo
assert {item["action"] for item in control_tower["detection"]["suggestedRepairActions"]} == {
    "sync_status"
}, demo
assert {item["externalMutation"] for item in control_tower["detection"]["suggestedRepairActions"]} == {
    False
}, demo
assert control_tower["detection"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-detections/preview"
), demo
assert control_tower["briefing"]["role"] == "accountant", demo
assert control_tower["briefing"]["riskLevel"] == "attention", demo
assert set(control_tower["briefing"]["sourceSystems"]) >= {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
}, demo
assert {item["type"] for item in control_tower["briefing"]["highlights"]} >= {
    "business_exception",
    "state_observation",
    "repair_context",
}, demo
assert {item["action"] for item in control_tower["briefing"]["recommendedActions"]} >= {
    "execute_repair_dry_run",
    "review_accounting_export",
}, demo
assert control_tower["briefing"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-briefings/preview"
), demo
assert {observation["system"] for observation in control_tower["observations"]} >= {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
}, demo
assert {business_exception["type"] for business_exception in control_tower["exceptions"]} == {
    "crm_payment_mismatch"
}, demo
assert {repair_action["action"] for repair_action in control_tower["repairActions"]} == {"sync_status"}, demo
assert {repair_action["externalMutation"] for repair_action in control_tower["repairActions"]} == {False}, demo
assert {step["step"] for step in control_tower["flow"]} >= {
    "observe",
    "detect",
    "propose",
    "approve",
    "execute",
}, demo
assert set(control_tower["metrics"]) >= {
    "drivedesk_business_state_observations",
    "drivedesk_business_exceptions",
    "drivedesk_repair_actions",
}, demo
assert control_tower["api"]["observe"] == "POST /tenants/{tenant_id}/business-state/observations", demo
assert control_tower["api"]["execute"] == "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute", demo
assert demo["engineeringProof"]["milestone"] == "engineering_70", demo
assert demo["engineeringProof"]["status"] == "validated", demo
assert len(demo["engineeringProof"]["summary"]) >= 4, demo
assert len(demo["engineeringProof"]["gates"]) >= 5, demo
assert {gate["name"] for gate in demo["engineeringProof"]["gates"]} >= {
    "Core smoke",
    "Public demo API",
    "Backup and restore",
    "Release safety",
    "GitOps and IaC",
}, demo
assert {item["kind"] for item in demo["engineeringProof"]["evidence"]} >= {"doc", "sdk"}, demo
assert any(
    item["path"] == "docs/public/SYSTEM_REVIEW_PATH.md"
    for item in demo["engineeringProof"]["evidence"]
), demo
assert any(
    item["path"] == "docs/public/REVIEWER_QUICKSTART.md"
    for item in demo["engineeringProof"]["evidence"]
), demo
assert {item["state"] for item in demo["integrationHealth"]} >= {
    "processed",
    "retry",
    "dead_letter",
    "matched",
    "open",
}
assert {item["evidence"] for item in demo["recoveryEvidence"]} >= {
    "backup_sha256_recorded",
    "restore_integrity_ok",
    "counts_match",
    "production_data_touched_false",
    "release.rollback.executed",
    "stable_release_healthy_after_rollback",
    "release.canary_gate.blocked",
    "promotion_blocked",
    "burn_rate_violation_detected",
    "release.staged_promotion.completed",
    "production_approval_recorded",
    "promotion_history_hash_recorded",
    "infra.scheduled_validation.healthy",
    "missed_run_guard_recorded",
    "infra.scheduled_validation.alerting.ready",
    "public-scheduled-validation-alert",
}, demo
assert all(item["state"] == "success" for item in demo["recoveryEvidence"]), demo
assert any(item["metric"] == "drivedesk_integration_reconciliations" for item in demo["integrationHealth"]), demo
assert any(item["metric"] == "drivedesk_integration_incidents" for item in demo["integrationHealth"]), demo
assert {adapter["key"] for adapter in demo["adapters"]} >= {
    "accounting.export.mock",
    "file.import.fake",
    "internal.noop",
}, demo
assert any(adapter.get("connectionProfileSupported") for adapter in demo["adapters"]), demo
assert any(adapter.get("requiredMappingKeys") for adapter in demo["adapters"]), demo
assert any(adapter.get("supportedConnectionScopes") for adapter in demo["adapters"]), demo
assert any(adapter.get("operationContracts") for adapter in demo["adapters"]), demo
assert len(demo["adapterScenarios"]) >= 4, demo
adapter_scenario_by_id = {scenario["id"]: scenario for scenario in demo["adapterScenarios"]}
assert set(adapter_scenario_by_id) >= {
    "adapter-file-import-preview",
    "adapter-file-import-execute",
    "adapter-accounting-export-retry",
    "adapter-dead-letter-review",
}, demo
assert {scenario["phase"] for scenario in demo["adapterScenarios"]} >= {
    "preview",
    "execute",
    "retry",
    "operator_review",
}, demo
assert {scenario["adapter"] for scenario in demo["adapterScenarios"]} >= {
    "file.import.fake",
    "accounting.export.mock",
}, demo
assert {scenario["requiredScope"] for scenario in demo["adapterScenarios"]} >= {
    "file_import:preview",
    "file_import:execute",
    "accounting:export",
}, demo
assert {
    output
    for scenario in demo["adapterScenarios"]
    for output in scenario["outputs"]
} >= {
    "mapping_preview",
    "outbox_event",
    "adapter_job",
    "retry_scheduled",
    "review_card",
    "manual_retry_endpoint",
}, demo
assert adapter_scenario_by_id["adapter-file-import-preview"]["endpoint"] == (
    "POST /tenants/{tenant_id}/integration-mapping-preview"
), demo
assert adapter_scenario_by_id["adapter-accounting-export-retry"]["status"] == "retry", demo
assert adapter_scenario_by_id["adapter-dead-letter-review"]["status"] == "dead_letter", demo
adapter_catalog = {adapter["key"]: adapter for adapter in adapters}
assert set(adapter_catalog) == {"accounting.export.mock", "file.import.fake", "internal.noop"}, adapters
runbook_catalog = {runbook["key"]: runbook for runbook in runbooks}
assert runbook_catalog["integration.retry_backlog"]["alert_name"] == "DriveDeskIntegrationRetries", runbooks
assert runbook_catalog["integration.dead_letter"]["source_statuses"] == ["dead_letter"], runbooks
assert runbook_catalog["integration.reconciliation_mismatch"]["source_statuses"] == ["mismatched"], runbooks
assert adapter_catalog["file.import.fake"]["direction"] == "inbound", adapters
assert adapter_catalog["file.import.fake"]["connection_profile_supported"] is True, adapters
assert adapter_catalog["file.import.fake"]["required_mapping_keys"] == ["external_id", "display_name"], adapters
assert adapter_catalog["file.import.fake"]["supported_connection_scopes"] == [
    "file_import:execute",
    "file_import:preview",
], adapters
assert adapter_catalog["file.import.fake"]["default_connection_scopes"] == [
    "file_import:execute",
    "file_import:preview",
], adapters
operation_contracts = {
    operation["key"]: operation
    for operation in adapter_catalog["file.import.fake"]["operation_contracts"]
}
assert operation_contracts["file_import_preview"]["required_connection_scope"] == "file_import:preview", adapters
assert operation_contracts["file_import_execute"]["required_connection_scope"] == "file_import:execute", adapters
assert operation_contracts["file_import_execute"]["event_type"] == "integration.file_import.requested", adapters
assert operation_contracts["file_import_execute"]["idempotency_keys"] == [
    "tenant_id",
    "source_name",
    "source_format",
    "records_hash",
], adapters
assert adapter_catalog["file.import.fake"]["mapping_example"]["external_id"] == "lead_id", adapters
assert "field mapping transform" in adapter_catalog["file.import.fake"]["capabilities"], adapters
assert "mapping preview" in adapter_catalog["file.import.fake"]["capabilities"], adapters
assert "connection scope enforcement" in adapter_catalog["file.import.fake"]["capabilities"], adapters
assert "records" in adapter_catalog["file.import.fake"]["payload_schema"]["required"], adapters
assert adapter_catalog["accounting.export.mock"]["direction"] == "outbound", adapters
assert adapter_catalog["accounting.export.mock"]["connection_profile_supported"] is True, adapters
assert adapter_catalog["accounting.export.mock"]["required_mapping_keys"] == [], adapters
assert adapter_catalog["accounting.export.mock"]["supported_connection_scopes"] == [
    "accounting:export",
], adapters
assert adapter_catalog["accounting.export.mock"]["default_connection_scopes"] == [
    "accounting:export",
], adapters
accounting_operation_contracts = {
    operation["key"]: operation
    for operation in adapter_catalog["accounting.export.mock"]["operation_contracts"]
}
assert set(accounting_operation_contracts) == {"accounting_export_execute"}, adapters
assert accounting_operation_contracts["accounting_export_execute"]["required_connection_scope"] == (
    "accounting:export"
), adapters
assert accounting_operation_contracts["accounting_export_execute"]["event_type"] == (
    "accounting.export.requested"
), adapters
assert accounting_operation_contracts["accounting_export_execute"]["endpoint"] == (
    "POST /tenants/{tenant_id}/integration-exports/accounting"
), adapters
assert accounting_operation_contracts["accounting_export_execute"]["idempotency_keys"] == [
    "tenant_id",
    "export_batch_id",
    "documents_hash",
], adapters
assert adapter_catalog["internal.noop"]["connection_profile_supported"] is False, adapters
assert adapter_catalog["internal.noop"]["supported_connection_scopes"] == [], adapters
lifecycle_catalog = {policy["record_type"]: policy for policy in lifecycle_policies}
assert set(lifecycle_catalog) == {"contract", "document", "lesson", "payment", "task"}, lifecycle_policies
assert lifecycle_catalog["contract"]["initial_status"] == "draft", lifecycle_policies
assert "completed" in lifecycle_catalog["contract"]["terminal_statuses"], lifecycle_policies
assert "confirmed" in lifecycle_catalog["payment"]["statuses"], lifecycle_policies
assert demo_headers.get("access-control-allow-origin") == "*", demo_headers
assert "public" in demo_headers.get("cache-control", ""), demo_headers
assert metrics_headers.get("content-type", "").startswith("text/plain"), metrics_headers
assert "drivedesk_metrics_storage_available " in metrics, metrics
assert "# HELP drivedesk_auth_sessions Current auth sessions by lifecycle status." in metrics, metrics
assert "# HELP drivedesk_auth_attempts_total Auth attempts grouped by outcome." in metrics, metrics
assert "# HELP drivedesk_business_records Current business records by type and status." in metrics, metrics
assert "# HELP drivedesk_workflow_rules Current workflow rules by status, trigger, and action." in metrics, metrics
assert "# HELP drivedesk_workflow_action_runs Workflow action runs by action type and status." in metrics, metrics
assert "# HELP drivedesk_integration_connections Integration connections by adapter and status." in metrics, metrics
assert "# HELP drivedesk_integration_connection_checks Integration connection health checks by adapter and status." in metrics, metrics
assert "# HELP drivedesk_integration_connection_check_duration_milliseconds Average integration connection check duration." in metrics, metrics
assert "# HELP drivedesk_integration_reconciliations Integration reconciliation results by adapter and status." in metrics, metrics
assert "# HELP drivedesk_integration_incidents Integration incidents by adapter, severity, and status." in metrics, metrics
assert "user_email" not in metrics, metrics
assert "token_id" not in metrics, metrics
assert "token_hash" not in metrics, metrics
assert "external_ref" not in metrics, metrics
assert "tenant_id" not in metrics, metrics
assert "/auth/login" in openapi["paths"], openapi["paths"].keys()
assert "/auth/me" in openapi["paths"], openapi["paths"].keys()
assert "/auth/logout" in openapi["paths"], openapi["paths"].keys()
assert "/auth/sessions" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-records" in openapi["paths"], openapi["paths"].keys()
assert "/business-record-lifecycle-policies" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-records/lifecycle-preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-records/{record_id}/transition" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/workflow-rules" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/workflow-action-runs" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/outbox-events/{event_id}/retry" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-connections" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-connections/{connection_id}/health" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-connections/{connection_id}/health-checks" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-reconciliations" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-incidents" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-incidents/{incident_id}/status" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-mapping-preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-operator-review" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/integration-exports/accounting" in openapi["paths"], openapi["paths"].keys()
assert "/integration-adapters" in openapi["paths"], openapi["paths"].keys()
assert "/integration-runbooks" in openapi["paths"], openapi["paths"].keys()
assert "/demo/public" in openapi["paths"], openapi["paths"].keys()
assert "/health" in openapi["paths"], openapi["paths"].keys()

if openapi_file.exists():
    generated = json.loads(openapi_file.read_text(encoding="utf-8"))
    assert "/demo/public" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/workflow-action-runs" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/outbox-events/{event_id}/retry" in generated["paths"], generated["paths"].keys()
    assert "/business-record-lifecycle-policies" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-records/lifecycle-preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-connections" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-connections/{connection_id}/health" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-connections/{connection_id}/health-checks" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-reconciliations" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-incidents" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-incidents/{incident_id}/status" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-mapping-preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-operator-review" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/integration-exports/accounting" in generated["paths"], generated["paths"].keys()
    assert "/integration-adapters" in generated["paths"], generated["paths"].keys()
    assert "/integration-runbooks" in generated["paths"], generated["paths"].keys()

print(
    "public demo API contract ok:",
    demo["tenant"]["slug"],
    demo["dataSource"],
    demo["workflow"]["currentStage"],
    len(demo["integrationHealth"]),
)
PY

BASE_URL="$BASE_URL" bash examples/curl/demo-public.sh
BASE_URL="$BASE_URL" "$PYTHON_BIN" examples/python/demo_public_client.py
BASE_URL="$BASE_URL" "$PYTHON_BIN" examples/python/demo_adapter_operation_plan.py

if command -v node >/dev/null 2>&1; then
  BASE_URL="$BASE_URL" node examples/js/demo-public-fetch.js
  BASE_URL="$BASE_URL" node examples/js/demo-adapter-operation-plan.mjs
else
  echo "node not available; skipped JS demo client"
fi

echo "public demo API smoke ok: $BASE_URL"
