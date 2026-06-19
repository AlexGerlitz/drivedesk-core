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

"$PYTHON_BIN" - <<'PY'
import json
import re
from pathlib import Path

from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

root = Path.cwd()
payload = build_public_demo_payload()
execution = payload.get("integrationExecution")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


require(isinstance(execution, dict), "integrationExecution payload missing")
require(execution.get("status") == "previewed", "execution status mismatch")
require(
    execution.get("command") == "POST /tenants/{tenant_id}/integration-executions/preview",
    "execution command mismatch",
)
require(execution.get("adapterKey") == "accounting.export.mock", "adapter mismatch")
require(execution.get("operationKey") == "accounting_export_execute", "operation mismatch")
require(execution.get("executionMode") == "contract_only", "execution mode mismatch")

summary = execution.get("summary", [])
require({item.get("label") for item in summary} >= {"Timeline", "Run ledger", "Provider calls", "Recovery"}, "summary labels missing")

ledger = execution.get("runLedger", {})
require(ledger.get("status") == "previewed", "ledger status mismatch")
require(ledger.get("wouldCreateWorkflowActionRun") is True, "workflow action run link missing")
require(ledger.get("wouldCreateOutboxEvent") is True, "outbox event link missing")
require(ledger.get("wouldCallProvider") is False, "provider call must be false")
require(ledger.get("externalMutation") is False, "ledger external mutation must be false")
require(ledger.get("rawPayloadIncluded") is False, "raw payload must not be included")
require(ledger.get("containsPii") is False, "PII must not be included")
require(ledger.get("evidence") == "integration_execution.run_ledger_prepared", "ledger evidence mismatch")

timeline = execution.get("timeline", [])
expected_stages = {
    "request_accepted",
    "runtime_preflight",
    "approval_gate",
    "outbox_enqueue",
    "worker_dispatch",
    "provider_call",
    "reconciliation",
    "operator_closure",
}
require({item.get("stage") for item in timeline} == expected_stages, "timeline stages mismatch")
for item in timeline:
    require(item.get("externalMutation") is False, f"timeline mutation leak: {item}")
    require(item.get("evidence", "").startswith("integration_execution."), f"timeline evidence mismatch: {item}")
provider_stage = next(item for item in timeline if item.get("stage") == "provider_call")
require(provider_stage.get("status") == "blocked_in_public_preview", "provider stage must be blocked")
require(provider_stage.get("providerCallEnabled") is False, "provider call enabled leak")

transitions = execution.get("stateTransitions", [])
require(len(transitions) >= 5, "state transitions missing")
require(transitions[0].get("from") == "none", "first transition mismatch")
require(transitions[-1].get("to") == "operator_review_ready", "final transition mismatch")

retry_policy = execution.get("retryPolicy", [])
require({item.get("name") for item in retry_policy} == {"retry_queue", "dead_letter_review"}, "retry policy mismatch")
require(any(item.get("trigger") == "outbox_event.retry_requested" for item in retry_policy), "retry trigger missing")
require(any(item.get("trigger") == "outbox.dead_letter" for item in retry_policy), "dead-letter trigger missing")

reconciliation = execution.get("reconciliationLinks", [])
require({item.get("name") for item in reconciliation} == {"expected_result", "provider_evidence", "mismatch_route"}, "reconciliation links mismatch")
require(any(item.get("wouldRecord") == "IntegrationIncident" for item in reconciliation), "incident route missing")

observability = execution.get("observability", [])
metrics = {item.get("metric") for item in observability}
require(
    metrics >= {
        "drivedesk_workflow_action_runs",
        "drivedesk_outbox_events",
        "drivedesk_integration_reconciliations",
        "drivedesk_integration_incidents",
    },
    "observability metrics missing",
)

boundaries = execution.get("dataBoundaries", [])
require({item.get("name") for item in boundaries} == {
    "preview_only_execution",
    "idempotency_without_payload",
    "provider_result_redaction",
    "operator_review_before_mutation",
}, "data boundaries mismatch")
for item in boundaries:
    require(item.get("externalMutation") is False, f"boundary mutation leak: {item}")
    require(item.get("rawPayloadIncluded") in {False, None}, f"raw payload leak: {item}")
    require(item.get("containsPii") in {False, None}, f"PII leak: {item}")

api = execution.get("api", {})
require(api.get("standalone") == "GET /demo/integration-execution", "standalone API mismatch")
require(api.get("preview") == "POST /tenants/{tenant_id}/integration-executions/preview", "preview API mismatch")
require(api.get("runtimePreview") == "POST /tenants/{tenant_id}/integration-runtime/preview", "runtime preview API mismatch")
require(api.get("workflowActionRuns") == "GET /tenants/{tenant_id}/workflow-action-runs", "workflow action runs API mismatch")
require(api.get("outbox") == "GET /tenants/{tenant_id}/outbox-events", "outbox API mismatch")
require(api.get("reconciliations") == "GET /tenants/{tenant_id}/integration-reconciliations", "reconciliation API mismatch")
require(api.get("incidents") == "GET /tenants/{tenant_id}/integration-incidents", "incidents API mismatch")

docs = execution.get("docs", [])
doc_paths = {item.get("path") for item in docs}
require("docs/public/INTEGRATION_EXECUTION.md" in doc_paths, "execution doc missing from payload")
require("docs/public/INTEGRATION_RUNTIME.md" in doc_paths, "runtime doc missing from payload")
require("docs/public/OUTBOX_RECOVERY.md" in doc_paths, "outbox recovery doc missing from payload")

static_data = root / "apps/admin/public-demo/demo-data.js"
if static_data.exists():
    text = static_data.read_text(encoding="utf-8")
    match = re.match(r"window\.DRIVEDESK_DEMO_DATA = (.*);\n?$", text, re.S)
    require(match is not None, "static demo data wrapper mismatch")
    static_payload = json.loads(match.group(1))
    require(static_payload.get("integrationExecution") == execution, "static demo data integrationExecution mismatch")

schema = json.loads((root / "docs/openapi.json").read_text(encoding="utf-8"))
paths = schema.get("paths", {})
require("/demo/integration-execution" in paths, "OpenAPI missing integration execution demo endpoint")
require("/tenants/{tenant_id}/integration-executions/preview" in paths, "OpenAPI missing integration execution preview endpoint")
require(
    paths["/demo/integration-execution"]["get"]["operationId"]
    == "integration_execution_demo_demo_integration_execution_get",
    "demo operation id mismatch",
)

generated_paths = build_app().openapi().get("paths", {})
require("/demo/integration-execution" in generated_paths, "generated OpenAPI missing demo endpoint")
require("/tenants/{tenant_id}/integration-executions/preview" in generated_paths, "generated OpenAPI missing preview endpoint")

html = (root / "apps/admin/public-demo/index.html").read_text(encoding="utf-8")
for token in [
    "integrationExecutionSummaryRows",
    "integrationExecutionLedgerRows",
    "integrationExecutionTimelineRows",
    "integrationExecutionStateRows",
    "integrationExecutionRecoveryRows",
    "integrationExecutionBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = (root / "apps/admin/public-demo/app.js").read_text(encoding="utf-8")
for token in [
    "fillIntegrationExecution",
    "integrationExecution",
    "integrationExecutionTimelineRows",
    "integrationExecutionRecoveryRows",
]:
    require(token in app_js, f"public demo JS missing {token}")

manifest = json.loads((root / "sdk/generated/public-demo/openapi-client-manifest.json").read_text(encoding="utf-8"))
execution_manifest = manifest.get("integration_execution", {})
require(execution_manifest.get("path") == "/demo/integration-execution", "SDK manifest execution path mismatch")
require(execution_manifest.get("operation_id") == "integration_execution_demo_demo_integration_execution_get", "SDK manifest execution operation mismatch")
require("integrationExecution" in manifest.get("required_fields", []), "SDK manifest missing public field")

doc_text = (root / "docs/public/INTEGRATION_EXECUTION.md").read_text(encoding="utf-8")
for token in [
    "GET /demo/integration-execution",
    "POST /tenants/{tenant_id}/integration-executions/preview",
    "WorkflowActionRun",
    "OutboxEvent",
    "IntegrationReconciliation",
    "IntegrationIncident",
    "bash scripts/check_public_integration_execution.sh",
]:
    require(token in doc_text, f"execution doc missing {token}")

for forbidden in [
    "access_token",
    "refresh_token",
    "client_secret",
    "BEGIN PRIVATE KEY",
    "provider_payload",
    "raw_provider_payload",
    "phone",
    "passport",
]:
    require(forbidden not in json.dumps(execution, ensure_ascii=False), f"forbidden token leaked: {forbidden}")

print(
    "public integration execution contract ok: "
    f"{len(timeline)} stages, {len(transitions)} transitions, {len(observability)} metrics"
)
PY
