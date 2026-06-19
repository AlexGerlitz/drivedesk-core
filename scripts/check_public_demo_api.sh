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
connector_replay_endpoint, connector_replay_headers = get_json("/demo/connector-fixture-replay")
business_intake_endpoint, business_intake_headers = get_json("/demo/business-intake-pipeline")
business_task_handoff_endpoint, business_task_handoff_headers = get_json("/demo/business-task-handoff")
business_notification_channels_endpoint, business_notification_channels_headers = get_json(
    "/demo/business-notification-channels"
)
business_context_assistant_endpoint, business_context_assistant_headers = get_json(
    "/demo/business-context-assistant"
)
business_scenario_endpoint, business_scenario_headers = get_json("/demo/business-scenario-replay")
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
    "Provider intake",
}, demo
provider_intake = control_tower["providerIntake"]
assert provider_intake["providerKey"] == "crm.bitrix24.mock", demo
assert provider_intake["sourceType"] == "crm_deal", demo
assert provider_intake["subject"] == "deal:DEAL-2026-001", demo
assert provider_intake["status"] == "mapped", demo
assert provider_intake["safePayload"] == {
    "amount_bucket": "1000-2000",
    "owner_role": "sales",
    "source_state": "invoice_sent",
}, demo
assert set(provider_intake["droppedKeys"]) >= {"access_token", "full_name", "phone"}, demo
assert provider_intake["normalizedObservation"]["wouldCreate"] == "BusinessStateObservation", demo
assert provider_intake["normalizedObservation"]["wouldRecordEvent"] == "business_state.observation.recorded", demo
assert {
    provider_intake["normalizedObservation"]["rawPayloadIncluded"],
    provider_intake["normalizedObservation"]["piiIncluded"],
    provider_intake["normalizedObservation"]["externalFetch"],
    provider_intake["normalizedObservation"]["externalMutation"],
    provider_intake["normalizedObservation"]["requiresSecret"],
} == {False}, demo
assert {item["name"] for item in provider_intake["dataBoundaries"]} == {
    "preview_only_no_persist",
    "raw_provider_payload_not_returned",
    "secret_boundary",
}, demo
assert {item["step"] for item in provider_intake["nextSteps"]} == {
    "record_normalized_observation",
    "open_workbench_context",
    "run_detection_preview",
}, demo
assert {item["externalMutation"] for item in provider_intake["nextSteps"]} == {False}, demo
assert provider_intake["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-provider-intake/preview"
), demo
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
assert control_tower["workbenchContext"]["contextKind"] == "role_assist", demo
assert control_tower["workbenchContext"]["role"] == "accountant", demo
assert control_tower["workbenchContext"]["riskLevel"] == "attention", demo
assert set(control_tower["workbenchContext"]["sourceSystems"]) >= {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
}, demo
assert {item["systemFamily"] for item in control_tower["workbenchContext"]["contextCards"]} == {
    "accounting",
    "bank",
    "crm",
}, demo
assert {item["piiIncluded"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}, demo
assert {item["rawPayloadIncluded"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}, demo
assert {item["externalFetch"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}, demo
assert {item["externalMutation"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}, demo
assert {item["action"] for item in control_tower["workbenchContext"]["suggestedActions"]} >= {
    "reconcile_crm_payment_status",
    "review_accounting_export",
    "open_action_plan_preview",
}, demo
assert {item["externalMutation"] for item in control_tower["workbenchContext"]["suggestedActions"]} == {
    False
}, demo
assert {item["name"] for item in control_tower["workbenchContext"]["dataBoundaries"]} == {
    "read_only_source_context",
    "pii_redaction",
    "secret_boundary",
}, demo
assert control_tower["workbenchContext"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-workbench-context/preview"
), demo
assert control_tower["escalation"]["policy"] == "exception_triage", demo
assert control_tower["escalation"]["riskLevel"] == "attention", demo
assert {item["queue"] for item in control_tower["escalation"]["queues"]} == {
    "finance_reconciliation"
}, demo
assert {item["ownerRole"] for item in control_tower["escalation"]["queues"]} == {"accountant"}, demo
assert {item["minSlaMinutes"] for item in control_tower["escalation"]["queues"]} == {120}, demo
assert {item["nextAction"] for item in control_tower["escalation"]["items"]} == {
    "execute_repair_dry_run"
}, demo
assert {item["externalMutation"] for item in control_tower["escalation"]["items"]} == {False}, demo
assert {item["action"] for item in control_tower["escalation"]["suggestedActions"]} == {
    "execute_repair_dry_run"
}, demo
assert control_tower["escalation"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-escalations/preview"
), demo
assert control_tower["actionPlan"]["planKind"] == "exception_resolution", demo
assert control_tower["actionPlan"]["role"] == "accountant", demo
assert control_tower["actionPlan"]["riskLevel"] == "attention", demo
assert {item["lane"] for item in control_tower["actionPlan"]["lanes"]} == {
    "finance_reconciliation"
}, demo
assert [item["step"] for item in control_tower["actionPlan"]["steps"]] == [
    "verify_source_evidence",
    "execute_repair_dry_run",
    "close_or_acknowledge_exception",
], demo
assert {item["externalMutation"] for item in control_tower["actionPlan"]["steps"]} == {False}, demo
assert {item["name"] for item in control_tower["actionPlan"]["automationCandidates"]} >= {
    "queue_repair_execution",
    "recheck_accounting_export",
}, demo
assert {item["status"] for item in control_tower["actionPlan"]["approvalGates"]} == {
    "satisfied"
}, demo
assert control_tower["actionPlan"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-action-plans/preview"
), demo
assert control_tower["notifications"]["notificationKind"] == "action_plan_updates", demo
assert control_tower["notifications"]["role"] == "accountant", demo
assert control_tower["notifications"]["riskLevel"] == "attention", demo
assert {item["channel"] for item in control_tower["notifications"]["channels"]} == {
    "in_app",
    "telegram",
}, demo
assert {item["externalDelivery"] for item in control_tower["notifications"]["channels"]} == {False}, demo
assert {item["piiIncluded"] for item in control_tower["notifications"]["drafts"]} == {False}, demo
assert {item["externalDelivery"] for item in control_tower["notifications"]["drafts"]} == {False}, demo
assert {item["sendMode"] for item in control_tower["notifications"]["deliveryPlan"]} == {
    "preview_only"
}, demo
assert {item["wouldEnqueueEvent"] for item in control_tower["notifications"]["deliveryPlan"]} == {
    "notification.delivery.requested"
}, demo
assert {item["name"] for item in control_tower["notifications"]["approvalGates"]} >= {
    "notification_content_review",
    "repair_action_approval",
}, demo
assert control_tower["notifications"]["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-notifications/preview"
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
    "intake",
    "observe",
    "context",
    "detect",
    "propose",
    "approve",
    "plan",
    "notify",
    "execute",
}, demo
assert set(control_tower["metrics"]) >= {
    "drivedesk_business_state_observations",
    "drivedesk_business_exceptions",
    "drivedesk_repair_actions",
}, demo
assert control_tower["api"]["observe"] == "POST /tenants/{tenant_id}/business-state/observations", demo
assert control_tower["api"]["intake"] == (
    "POST /tenants/{tenant_id}/business-provider-intake/preview"
), demo
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
    "crm.bitrix24.mock",
    "file.import.fake",
    "internal.noop",
}, demo
assert any(adapter.get("connectionProfileSupported") for adapter in demo["adapters"]), demo
assert any(adapter.get("requiredMappingKeys") for adapter in demo["adapters"]), demo
assert any(adapter.get("supportedConnectionScopes") for adapter in demo["adapters"]), demo
assert any(adapter.get("operationContracts") for adapter in demo["adapters"]), demo
demo_adapter_catalog = {adapter["key"]: adapter for adapter in demo["adapters"]}
demo_crm_auth = demo_adapter_catalog["crm.bitrix24.mock"]["authProfile"]
assert demo_crm_auth["mode"] == "oauth2_or_webhook_boundary", demo
assert demo_crm_auth["publicDemoRequiresSecret"] is False, demo
assert demo_crm_auth["realProviderRequiresSecret"] is True, demo
assert demo_crm_auth["credentialPlacement"] == "server_secret_store", demo
assert demo_crm_auth["tokenExchange"] == "private_connector_only", demo
assert "no_browser_token_storage" in demo_crm_auth["dataBoundaries"], demo
assert len(demo["adapterScenarios"]) >= 4, demo
adapter_scenario_by_id = {scenario["id"]: scenario for scenario in demo["adapterScenarios"]}
assert set(adapter_scenario_by_id) >= {
    "adapter-crm-deal-ingest",
    "adapter-crm-deal-preview",
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
    "crm.bitrix24.mock",
    "file.import.fake",
    "accounting.export.mock",
}, demo
assert {scenario["requiredScope"] for scenario in demo["adapterScenarios"]} >= {
    "crm:deal.ingest",
    "crm:deal.preview",
    "file_import:preview",
    "file_import:execute",
    "accounting:export",
}, demo
assert {
    output
    for scenario in demo["adapterScenarios"]
    for output in scenario["outputs"]
} >= {
    "normalized_observation",
    "redaction_evidence",
    "safe_payload",
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
assert adapter_scenario_by_id["adapter-crm-deal-preview"]["endpoint"] == (
    "POST /tenants/{tenant_id}/business-provider-intake/preview"
), demo
assert adapter_scenario_by_id["adapter-crm-deal-ingest"]["operation"] == "crm_deal_ingest_execute", demo
assert adapter_scenario_by_id["adapter-accounting-export-retry"]["status"] == "retry", demo
assert adapter_scenario_by_id["adapter-dead-letter-review"]["status"] == "dead_letter", demo
adapter_studio = demo["adapterStudio"]
assert {item["label"] for item in adapter_studio["summary"]} >= {
    "SDK plans",
    "CRM preview",
    "Worker ingest",
    "Secrets",
}, demo
assert {item["evidence"] for item in adapter_studio["flow"]} >= {
    "GET /integration-adapters",
    "sdk/generated/public-demo/",
    "business_provider_intake.previewed",
    "integration.crm_deal.ingest.requested",
    "drivedesk_integration_incidents",
}, demo
studio_plans = {item["scenarioId"]: item for item in adapter_studio["operationPlans"]}
assert set(studio_plans) == {"adapter-crm-deal-preview", "adapter-crm-deal-ingest"}, demo
assert studio_plans["adapter-crm-deal-preview"]["operation"] == "crm_deal_intake_preview", demo
assert studio_plans["adapter-crm-deal-preview"]["endpoint"] == (
    "POST /tenants/{tenant_id}/business-provider-intake/preview"
), demo
assert studio_plans["adapter-crm-deal-preview"]["executionMode"] == "contract_only", demo
assert studio_plans["adapter-crm-deal-preview"]["safeToRunAgainstPublicDemo"] is False, demo
assert studio_plans["adapter-crm-deal-ingest"]["method"] == "WORKER", demo
assert studio_plans["adapter-crm-deal-ingest"]["endpoint"] == (
    "worker:drivedesk_worker.main.process_pending_outbox"
), demo
assert {item["evidence"] for item in adapter_studio["boundaries"]} >= {
    "server_secret_store",
    "private_connector_only",
    "redaction_evidence",
    "safeToRunAgainstPublicDemo=false",
}, demo
assert {item["metric"] for item in adapter_studio["diagnostics"]} >= {
    "drivedesk_integration_connection_checks",
    "drivedesk_integration_reconciliations",
    "drivedesk_integration_incidents",
    "integration.operator_review.created",
}, demo
assert {item["path"] for item in adapter_studio["docs"]} >= {
    "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
}, demo
connector_replay = demo["connectorFixtureReplay"]
assert connector_replay_endpoint == connector_replay, connector_replay_endpoint
assert connector_replay_headers["access-control-allow-origin"] == "*", connector_replay_headers
assert connector_replay_headers["cache-control"] == "public, max-age=60", connector_replay_headers
assert connector_replay["status"] == "validated", demo
assert connector_replay["command"] == "bash scripts/check_public_connector_fixture_replay.sh", demo
assert connector_replay["fixtureFile"] == "examples/connector-fixtures/replay-fixtures.sanitized.json", demo
assert connector_replay["evidenceFile"] == "docs/public/evidence/connector-fixture-replay.sanitized.json", demo
assert {item["label"] for item in connector_replay["summary"]} >= {
    "Fixture groups",
    "Provider calls",
    "Secrets",
    "Operator path",
}, demo
replay_outcomes = {item["group"]: item for item in connector_replay["outcomes"]}
assert set(replay_outcomes) == {
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
}, demo
assert replay_outcomes["happy_path_preview"]["evidence"] == "safe_payload_present=true", demo
assert replay_outcomes["sensitive_payload_redaction"]["evidence"] == "redaction_evidence_present=true", demo
assert replay_outcomes["invalid_payload"]["evidence"] == "outbox_event_created=false", demo
assert replay_outcomes["retryable_provider_failure"]["status"] == "retry_scheduled", demo
assert replay_outcomes["dead_letter_provider_failure"]["evidence"] == "integration.operator_review.created", demo
assert replay_outcomes["reconciliation_mismatch"]["evidence"] == "drivedesk_integration_reconciliations", demo
assert {item["state"] for item in connector_replay["boundaries"]} >= {
    "not_returned",
    "disabled",
}, demo
assert {item["path"] for item in connector_replay["docs"]} >= {
    "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
    "docs/public/evidence/connector-fixture-replay.sanitized.json",
    "examples/connector-fixtures/replay-fixtures.sanitized.json",
}, demo
business_intake = demo["businessIntakePipeline"]
assert business_intake_endpoint == business_intake, business_intake_endpoint
assert business_intake_headers["access-control-allow-origin"] == "*", business_intake_headers
assert business_intake_headers["cache-control"] == "public, max-age=60", business_intake_headers
assert business_intake["status"] == "previewed", demo
assert business_intake["command"] == "POST /tenants/{tenant_id}/business-intake-pipeline/preview", demo
assert {item["label"] for item in business_intake["summary"]} >= {
    "Provider events",
    "Dropped unsafe keys",
    "Detected exceptions",
    "External writes",
}, demo
assert set(business_intake["sourceSystems"]) == {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
}, demo
intake_by_provider = {item["providerKey"]: item for item in business_intake["intakePreviews"]}
assert set(intake_by_provider) == {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
}, demo
assert set(intake_by_provider["crm.bitrix24.mock"]["droppedKeys"]) >= {
    "access_token",
    "full_name",
    "phone",
}, demo
assert set(intake_by_provider["bank.statement.mock"]["droppedKeys"]) >= {"payer_phone"}, demo
assert set(intake_by_provider["accounting.export.mock"]["droppedKeys"]) >= {"session_secret"}, demo
assert {card["systemFamily"] for card in business_intake["workbench"]["contextCards"]} == {
    "crm",
    "bank",
    "accounting",
}, demo
assert {card["rawPayloadIncluded"] for card in business_intake["workbench"]["contextCards"]} == {False}, demo
assert {card["piiIncluded"] for card in business_intake["workbench"]["contextCards"]} == {False}, demo
assert {card["externalMutation"] for card in business_intake["workbench"]["contextCards"]} == {False}, demo
assert business_intake["detections"]["status"] == "detected", demo
assert {
    item["exceptionType"] for item in business_intake["detections"]["detectedExceptions"]
} >= {"crm_payment_mismatch"}, demo
assert {
    item["requiresApproval"] for item in business_intake["detections"]["suggestedRepairActions"]
} == {True}, demo
assert {step["step"] for step in business_intake["actionPlan"]["steps"]} >= {
    "normalize_provider_events",
    "open_role_workbench",
    "review_detected_exceptions",
    "prepare_approval_gated_repair",
}, demo
assert {gate["gate"] for gate in business_intake["actionPlan"]["approvalGates"]} >= {
    "external_write_gate",
    "notification_delivery_gate",
}, demo
assert business_intake["notifications"]["status"] == "draft_only", demo
assert business_intake["notifications"]["externalDelivery"] is False, demo
assert business_intake["notifications"]["containsPii"] is False, demo
assert {item["name"] for item in business_intake["dataBoundaries"]} == {
    "no_external_calls",
    "no_persistence",
    "secret_and_pii_boundary",
}, demo
assert {item["path"] for item in business_intake["docs"]} >= {
    "docs/public/BUSINESS_INTAKE_PIPELINE.md",
    "docs/public/BUSINESS_CONTROL_TOWER.md",
    "docs/public/API_BACKED_DEMO.md",
}, demo
business_task_handoff = demo["businessTaskHandoff"]
assert business_task_handoff_endpoint == business_task_handoff, business_task_handoff_endpoint
assert business_task_handoff_headers["access-control-allow-origin"] == "*", business_task_handoff_headers
assert business_task_handoff_headers["cache-control"] == "public, max-age=60", business_task_handoff_headers
assert business_task_handoff["status"] == "previewed", demo
assert (
    business_task_handoff["command"]
    == "POST /tenants/{tenant_id}/business-task-handoffs/preview"
), demo
assert {item["label"] for item in business_task_handoff["summary"]} >= {
    "Task cards",
    "Internal outbox",
    "Draft notifications",
    "External writes",
}, demo
assert business_task_handoff["role"] == "accountant", demo
assert business_task_handoff["subject"] == "deal:DEAL-2026-001", demo
assert len(business_task_handoff["taskCards"]) == 2, demo
assert len(business_task_handoff["outboxCandidates"]) == 2, demo
assert len(business_task_handoff["notificationDrafts"]) == 2, demo
assert {card["status"] for card in business_task_handoff["taskCards"]} == {"would_create"}, demo
assert {card["wouldCreate"] for card in business_task_handoff["taskCards"]} == {
    "BusinessRecord(type=task)"
}, demo
assert {card["externalMutation"] for card in business_task_handoff["taskCards"]} == {False}, demo
assert {card["containsPii"] for card in business_task_handoff["taskCards"]} == {False}, demo
assert {card["rawPayloadIncluded"] for card in business_task_handoff["taskCards"]} == {False}, demo
assert {
    candidate["eventType"] for candidate in business_task_handoff["outboxCandidates"]
} == {"task.created"}, demo
assert {
    candidate["adapterKey"] for candidate in business_task_handoff["outboxCandidates"]
} == {"internal.noop"}, demo
assert {
    candidate["status"] for candidate in business_task_handoff["outboxCandidates"]
} == {"would_enqueue"}, demo
assert {
    candidate["externalMutation"] for candidate in business_task_handoff["outboxCandidates"]
} == {False}, demo
assert {
    draft["status"] for draft in business_task_handoff["notificationDrafts"]
} == {"draft_only"}, demo
assert {
    draft["externalDelivery"] for draft in business_task_handoff["notificationDrafts"]
} == {False}, demo
assert {draft["containsPii"] for draft in business_task_handoff["notificationDrafts"]} == {False}, demo
assert {item["gate"] for item in business_task_handoff["approvalGates"]} == {
    "task_creation_review",
    "external_write_gate",
    "repair_action_approval",
}, demo
assert {item["name"] for item in business_task_handoff["dataBoundaries"]} == {
    "preview_only_no_persistence",
    "internal_only_outbox",
    "safe_task_payload",
}, demo
assert {item["path"] for item in business_task_handoff["docs"]} >= {
    "docs/public/BUSINESS_TASK_HANDOFF.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/BUSINESS_INTAKE_PIPELINE.md",
}, demo
business_notification_channels = demo["businessNotificationChannels"]
assert business_notification_channels_endpoint == business_notification_channels, (
    business_notification_channels_endpoint
)
assert (
    business_notification_channels_headers["access-control-allow-origin"] == "*"
), business_notification_channels_headers
assert (
    business_notification_channels_headers["cache-control"] == "public, max-age=60"
), business_notification_channels_headers
assert business_notification_channels["status"] == "previewed", demo
assert (
    business_notification_channels["command"]
    == "POST /tenants/{tenant_id}/business-notification-channels/preview"
), demo
assert {item["label"] for item in business_notification_channels["summary"]} >= {
    "Channels",
    "Internal ready",
    "Draft-only external",
    "External deliveries",
}, demo
assert business_notification_channels["role"] == "accountant", demo
assert business_notification_channels["subject"] == "deal:DEAL-2026-001", demo
channel_by_key = {item["channel"]: item for item in business_notification_channels["channels"]}
assert set(channel_by_key) == {"in_app", "telegram", "email", "sms", "webhook"}, demo
assert channel_by_key["in_app"]["status"] == "ready", demo
assert channel_by_key["in_app"]["configured"] is True, demo
assert channel_by_key["in_app"]["requiresSecret"] is False, demo
assert channel_by_key["in_app"]["requiresPrivateConnector"] is False, demo
assert {
    channel_by_key[channel]["status"]
    for channel in ["telegram", "email", "sms", "webhook"]
} == {"requires_private_secret", "requires_private_provider", "requires_private_endpoint"}, demo
assert {
    channel_by_key[channel]["requiresSecret"]
    for channel in ["telegram", "email", "sms", "webhook"]
} == {True}, demo
assert {
    channel_by_key[channel]["requiresPrivateConnector"]
    for channel in ["telegram", "email", "sms", "webhook"]
} == {True}, demo
assert {
    item["externalDelivery"] for item in business_notification_channels["channels"]
} == {False}, demo
assert {
    item["containsPii"] for item in business_notification_channels["channels"]
} == {False}, demo
assert {
    item["rawPayloadIncluded"] for item in business_notification_channels["channels"]
} == {False}, demo
assert {item["rule"] for item in business_notification_channels["routingRules"]} == {
    "prefer_internal_in_app",
    "external_channels_require_private_connector",
    "safe_payload_only",
}, demo
assert len(business_notification_channels["deliveryDrafts"]) == 5, demo
assert {
    item["wouldEnqueueEvent"] for item in business_notification_channels["deliveryDrafts"]
} == {"notification.delivery.requested"}, demo
assert {
    item["externalDelivery"] for item in business_notification_channels["deliveryDrafts"]
} == {False}, demo
assert {
    item["containsPii"] for item in business_notification_channels["deliveryDrafts"]
} == {False}, demo
assert {
    item["rawPayloadIncluded"] for item in business_notification_channels["deliveryDrafts"]
} == {False}, demo
assert {item["gate"] for item in business_notification_channels["approvalGates"]} == {
    "notification_content_review",
    "private_channel_secret_setup",
    "external_delivery_gate",
}, demo
assert {item["name"] for item in business_notification_channels["dataBoundaries"]} == {
    "preview_only_no_delivery",
    "server_secret_store_boundary",
    "safe_notification_payload",
}, demo
assert {item["path"] for item in business_notification_channels["docs"]} >= {
    "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md",
    "docs/public/BUSINESS_TASK_HANDOFF.md",
    "docs/public/API_BACKED_DEMO.md",
}, demo
business_context_assistant = demo["businessContextAssistant"]
assert business_context_assistant_endpoint == business_context_assistant, business_context_assistant_endpoint
assert (
    business_context_assistant_headers["access-control-allow-origin"] == "*"
), business_context_assistant_headers
assert (
    business_context_assistant_headers["cache-control"] == "public, max-age=60"
), business_context_assistant_headers
assert business_context_assistant["status"] == "previewed", demo
assert (
    business_context_assistant["command"]
    == "POST /tenants/{tenant_id}/business-workbench-context/preview"
), demo
assert {item["label"] for item in business_context_assistant["summary"]} >= {
    "Context cards",
    "Source systems",
    "Suggested actions",
    "External writes",
}, demo
assert business_context_assistant["role"] == "accountant", demo
assert business_context_assistant["subject"] == "deal:DEAL-2026-001", demo
assert set(business_context_assistant["sourceSystems"]) == {
    "crm.bitrix24.mock",
    "bank.statement.mock",
    "accounting.export.mock",
    "legal.reference.mock",
}, demo
assert {item["systemFamily"] for item in business_context_assistant["contextCards"]} == {
    "crm",
    "bank",
    "accounting",
    "legal",
}, demo
assert {item["externalFetch"] for item in business_context_assistant["contextCards"]} == {False}, demo
assert {item["externalMutation"] for item in business_context_assistant["contextCards"]} == {False}, demo
assert {item["containsPii"] for item in business_context_assistant["contextCards"]} == {False}, demo
assert {item["rawPayloadIncluded"] for item in business_context_assistant["contextCards"]} == {False}, demo
assert {
    item.get("fullTextIncluded", False)
    for item in business_context_assistant["contextCards"]
    if item["systemFamily"] == "legal"
} == {False}, demo
assert {item["rule"] for item in business_context_assistant["insightRules"]} == {
    "correlate_payment_evidence",
    "detect_accounting_export_gap",
    "attach_policy_reference",
}, demo
assert {item["externalMutation"] for item in business_context_assistant["insightRules"]} == {False}, demo
assert {item["action"] for item in business_context_assistant["suggestedActions"]} == {
    "open_reconciliation_plan",
    "queue_accounting_export_after_review",
    "attach_policy_reference",
    "prepare_internal_notification",
}, demo
assert {item["externalMutation"] for item in business_context_assistant["suggestedActions"]} == {
    False
}, demo
assert {item["name"] for item in business_context_assistant["dataBoundaries"]} == {
    "read_only_context_preview",
    "no_raw_provider_payload",
    "secret_boundary",
    "legal_reference_link_only",
}, demo
assert business_context_assistant["api"]["standalone"] == "GET /demo/business-context-assistant", demo
assert business_context_assistant["api"]["preview"] == (
    "POST /tenants/{tenant_id}/business-workbench-context/preview"
), demo
assert {item["path"] for item in business_context_assistant["docs"]} >= {
    "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
    "docs/public/BUSINESS_CONTROL_TOWER.md",
    "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
}, demo
business_scenario_replay = demo["businessScenarioReplay"]
assert business_scenario_endpoint == business_scenario_replay, business_scenario_endpoint
assert business_scenario_headers["access-control-allow-origin"] == "*", business_scenario_headers
assert business_scenario_headers["cache-control"] == "public, max-age=60", business_scenario_headers
assert business_scenario_replay["status"] == "validated", demo
assert business_scenario_replay["command"] == "bash scripts/check_public_business_scenario_replay.sh", demo
assert {item["label"] for item in business_scenario_replay["summary"]} >= {
    "Scenario groups",
    "Source systems",
    "Operator actions",
    "External writes",
}, demo
scenario_replay_by_id = {item["id"]: item for item in business_scenario_replay["scenarios"]}
assert set(scenario_replay_by_id) == {
    "crm-bank-payment-mismatch",
    "support-sla-risk",
    "procurement-delay-risk",
}, demo
assert {item["stage"] for item in business_scenario_replay["flow"]} == {
    "signal",
    "normalize",
    "detect",
    "plan",
    "execute",
}, demo
assert {item["path"] for item in business_scenario_replay["docs"]} >= {
    "docs/public/BUSINESS_SCENARIO_REPLAY.md",
    "docs/public/BUSINESS_CONTROL_TOWER.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
}, demo
for scenario in scenario_replay_by_id.values():
    assert scenario["normalizedFacts"], scenario
    assert scenario["recommendedActions"], scenario
    assert scenario["automationCandidates"], scenario
    assert any(item["safeToAutoRun"] is False for item in scenario["automationCandidates"]), scenario
adapter_catalog = {adapter["key"]: adapter for adapter in adapters}
assert set(adapter_catalog) == {
    "accounting.export.mock",
    "crm.bitrix24.mock",
    "file.import.fake",
    "internal.noop",
}, adapters
crm_contracts = {
    contract["key"]: contract for contract in adapter_catalog["crm.bitrix24.mock"]["operation_contracts"]
}
assert crm_contracts["crm_deal_intake_preview"]["required_connection_scope"] == "crm:deal.preview", adapters
assert crm_contracts["crm_deal_ingest_execute"]["required_connection_scope"] == "crm:deal.ingest", adapters
crm_auth = adapter_catalog["crm.bitrix24.mock"]["auth_profile"]
assert crm_auth["mode"] == "oauth2_or_webhook_boundary", adapters
assert crm_auth["public_demo_requires_secret"] is False, adapters
assert crm_auth["real_provider_requires_secret"] is True, adapters
assert crm_auth["credential_placement"] == "server_secret_store", adapters
assert crm_auth["token_exchange"] == "private_connector_only", adapters
assert "no_browser_token_storage" in crm_auth["data_boundaries"], adapters
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
assert "/tenants/{tenant_id}/business-provider-intake/preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-workbench-context/preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-action-plans/preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-notifications/preview" in openapi["paths"], openapi["paths"].keys()
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
assert "/demo/connector-fixture-replay" in openapi["paths"], openapi["paths"].keys()
assert "/demo/business-intake-pipeline" in openapi["paths"], openapi["paths"].keys()
assert "/demo/business-task-handoff" in openapi["paths"], openapi["paths"].keys()
assert "/demo/business-notification-channels" in openapi["paths"], openapi["paths"].keys()
assert "/demo/business-context-assistant" in openapi["paths"], openapi["paths"].keys()
assert "/demo/business-scenario-replay" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-intake-pipeline/preview" in openapi["paths"], openapi["paths"].keys()
assert "/tenants/{tenant_id}/business-task-handoffs/preview" in openapi["paths"], openapi["paths"].keys()
assert (
    "/tenants/{tenant_id}/business-notification-channels/preview" in openapi["paths"]
), openapi["paths"].keys()
assert "/health" in openapi["paths"], openapi["paths"].keys()

if openapi_file.exists():
    generated = json.loads(openapi_file.read_text(encoding="utf-8"))
    assert "/demo/public" in generated["paths"], generated["paths"].keys()
    assert "/demo/connector-fixture-replay" in generated["paths"], generated["paths"].keys()
    assert "/demo/business-intake-pipeline" in generated["paths"], generated["paths"].keys()
    assert "/demo/business-task-handoff" in generated["paths"], generated["paths"].keys()
    assert "/demo/business-notification-channels" in generated["paths"], generated["paths"].keys()
    assert "/demo/business-context-assistant" in generated["paths"], generated["paths"].keys()
    assert "/demo/business-scenario-replay" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-intake-pipeline/preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-task-handoffs/preview" in generated["paths"], generated["paths"].keys()
    assert (
        "/tenants/{tenant_id}/business-notification-channels/preview" in generated["paths"]
    ), generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-action-plans/preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-notifications/preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/workflow-action-runs" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/outbox-events/{event_id}/retry" in generated["paths"], generated["paths"].keys()
    assert "/business-record-lifecycle-policies" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-records/lifecycle-preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-provider-intake/preview" in generated["paths"], generated["paths"].keys()
    assert "/tenants/{tenant_id}/business-workbench-context/preview" in generated["paths"], generated["paths"].keys()
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
