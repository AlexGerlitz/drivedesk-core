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

"$PYTHON_BIN" - <<'PY' "$ROOT"
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

root = Path(sys.argv[1])
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def parse_static_demo_data(path: Path) -> dict[str, object]:
    text = read(path)
    match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", text, re.S)
    require(match is not None, "static demo data assignment not found")
    return json.loads(match.group(1)) if match else {}


doc_path = root / "docs/public/BUSINESS_ACTION_EXECUTION.md"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
system_review_path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
roadmap_path = root / "docs/public/ROADMAP.md"
client_sdk_doc_path = root / "docs/public/CLIENT_SDK.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
openapi_path = root / "docs/openapi.json"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
services_path = root / "apps/api/drivedesk_api/services.py"
export_script_path = root / "scripts/export_public_repo.sh"
ci_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
sdk_generator_path = root / "scripts/generate_public_demo_sdk.py"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [
    doc_path,
    api_demo_doc_path,
    capability_map_path,
    status_path,
    docs_readme_path,
    platform_tour_path,
    system_review_path,
    roadmap_path,
    client_sdk_doc_path,
    demo_data_path,
    demo_html_path,
    demo_app_path,
    openapi_path,
    schemas_path,
    main_path,
    services_path,
    sdk_generator_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
execution = api_payload.get("businessActionExecution", {})
static_execution = static_payload.get("businessActionExecution", {})

require(execution == static_execution, "API and static businessActionExecution differ")
require(execution.get("status") == "previewed", "businessActionExecution status mismatch")
require(
    execution.get("command") == "POST /tenants/{tenant_id}/business-action-executions/preview",
    "businessActionExecution command mismatch",
)
require(execution.get("role") == "accountant", "businessActionExecution role mismatch")
require(execution.get("subject") == "deal:DEAL-2026-001", "businessActionExecution subject mismatch")
require(
    {item.get("label") for item in execution.get("summary", [])}
    >= {"Execution plans", "Preflight checks", "Approval gates", "External writes"},
    "businessActionExecution summary missing required labels",
)

plans = execution.get("executionPlan", [])
require(len(plans) == 3, "execution plan count mismatch")
require(
    {item.get("action") for item in plans}
    == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "prepare_internal_notification",
    },
    "execution actions mismatch",
)
require(
    {item.get("wouldEnqueueEvent") for item in plans}
    == {
        "business.action.review_requested",
        "accounting.export.requested",
        "notification.delivery.requested",
    },
    "execution events mismatch",
)
for item in plans:
    require(item.get("dryRun") is True, f"execution plan must be dry-run: {item}")
    require(item.get("externalMutation") is False, f"execution plan mutates externally: {item}")
    require(item.get("containsPii") is False, f"execution plan contains PII: {item}")
    require(item.get("rawPayloadIncluded") is False, f"execution plan includes raw payload: {item}")
    require(str(item.get("idempotencyKey", "")).startswith("business-action-execution:"), f"idempotency key mismatch: {item}")
    require(item.get("safePayloadProfile") == "role_subject_action_reference", f"payload profile mismatch: {item}")
    require(item.get("evidence") == "business_action_execution.previewed", f"evidence mismatch: {item}")

require(
    any(item.get("commitWouldMutateProvider") is True for item in plans),
    "execution plan must model provider-changing commit candidate",
)
require(
    any(item.get("safeToAutoRun") is False for item in plans),
    "execution plan must keep at least one candidate behind approval",
)

preflight = execution.get("preflightChecks", [])
require(
    {item.get("check") for item in preflight}
    == {
        "safe_payload_profile",
        "idempotency_key_ready",
        "approval_gate_attached",
        "connector_secret_boundary",
    },
    "preflight checks mismatch",
)
for item in preflight:
    require(item.get("externalMutation") is False, f"preflight mutates externally: {item}")
    require(item.get("evidence") == "business_action_execution.previewed", f"preflight evidence mismatch: {item}")

dry_runs = execution.get("dryRunResults", [])
require(len(dry_runs) == 3, "dry-run result count mismatch")
for item in dry_runs:
    require(item.get("wouldRecord") == "WorkflowActionRun", f"dry-run record target mismatch: {item}")
    require(item.get("status") == "would_enqueue", f"dry-run status mismatch: {item}")
    require(item.get("externalMutation") is False, f"dry-run mutates externally: {item}")
    require(item.get("containsPii") is False, f"dry-run contains PII: {item}")
    require(item.get("rawPayloadIncluded") is False, f"dry-run includes raw payload: {item}")

require(
    {item.get("gate") for item in execution.get("approvalGates", [])}
    == {"operator_review_gate", "external_write_gate", "idempotent_outbox_gate"},
    "approval gates mismatch",
)
require(
    {item.get("step") for item in execution.get("rollbackPlan", [])}
    == {"preview_has_no_rollback", "commit_uses_outbox_recovery"},
    "rollback plan mismatch",
)
require(
    {item.get("name") for item in execution.get("dataBoundaries", [])}
    == {"dry_run_only", "no_provider_write", "safe_execution_payload", "audit_and_outbox_contract"},
    "data boundaries mismatch",
)

require(execution.get("api", {}).get("standalone") == "GET /demo/business-action-execution", "standalone API link mismatch")
require(
    execution.get("api", {}).get("preview") == "POST /tenants/{tenant_id}/business-action-executions/preview",
    "preview API link mismatch",
)
require(
    {item.get("path") for item in execution.get("docs", [])}
    >= {
        "docs/public/BUSINESS_ACTION_EXECUTION.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
    },
    "businessActionExecution docs mismatch",
)

serialized = json.dumps(execution, ensure_ascii=False, sort_keys=True).lower()
for blocked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization", "access_token"]:
    require(blocked not in serialized, f"businessActionExecution leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-action-execution" in paths, "OpenAPI missing action execution demo endpoint")
require(
    "/tenants/{tenant_id}/business-action-executions/preview" in paths,
    "OpenAPI missing action execution preview endpoint",
)
require(
    paths.get("/demo/business-action-execution", {}).get("get", {}).get("operationId")
    == "business_action_execution_demo_demo_business_action_execution_get",
    "action execution demo operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require("BusinessActionExecutionDemoRead" in components, "OpenAPI missing BusinessActionExecutionDemoRead schema")
require("BusinessActionExecutionPreviewRead" in components, "OpenAPI missing BusinessActionExecutionPreviewRead schema")
require(
    "businessActionExecution"
    in components.get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessActionExecution",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-action-execution" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing action execution demo",
)
require(
    "/tenants/{tenant_id}/business-action-executions/preview" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing action execution preview",
)

html = read(demo_html_path)
for token in [
    "Action Execution",
    "businessActionExecutionSummaryRows",
    "businessActionExecutionPlanRows",
    "businessActionExecutionPreflightRows",
    "businessActionExecutionDryRunRows",
    "businessActionExecutionBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessActionExecution",
    "fillBusinessActionExecution",
    "businessActionExecutionSummaryRows",
    "businessActionExecutionPlanRows",
    "businessActionExecutionPreflightRows",
    "businessActionExecutionDryRunRows",
    "businessActionExecutionBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

sdk_generator = read(sdk_generator_path)
for token in [
    "BUSINESS_ACTION_EXECUTION_PATH",
    "business_action_execution_operation",
    "BusinessActionExecutionDemoRead",
    "business_action_execution",
]:
    require(token in sdk_generator, f"SDK generator missing {token}")

if sdk_manifest_path.is_file():
    manifest = json.loads(read(sdk_manifest_path))
    execution_manifest = manifest.get("business_action_execution", {})
    require(execution_manifest.get("path") == "/demo/business-action-execution", "SDK manifest execution path mismatch")
    require(execution_manifest.get("method") == "GET", "SDK manifest execution method mismatch")
    require(
        execution_manifest.get("operation_id")
        == "business_action_execution_demo_demo_business_action_execution_get",
        "SDK manifest execution operation mismatch",
    )
    require(
        "businessActionExecution" in manifest.get("required_fields", []),
        "SDK manifest public demo required fields missing execution",
    )

for path, name in [
    (doc_path, "business action execution doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (docs_readme_path, "public docs README"),
    (platform_tour_path, "platform tour"),
    (system_review_path, "system review path"),
    (roadmap_path, "roadmap"),
    (client_sdk_doc_path, "client SDK doc"),
]:
    text = read(path)
    require("BUSINESS_ACTION_EXECUTION.md" in text, f"{name} missing action execution doc link")
    require("businessActionExecution" in text, f"{name} missing businessActionExecution token")
    require("GET /demo/business-action-execution" in text, f"{name} missing standalone endpoint")

require("/demo/business-action-execution" in read(main_path), "API main missing action execution demo route")
require("/business-action-executions/preview" in read(main_path), "API main missing action execution preview route")
require("preview_business_action_execution" in read(services_path), "services missing action execution implementation")
require("BusinessActionExecutionPreviewRead" in read(schemas_path), "schemas missing BusinessActionExecutionPreviewRead")

if is_public_export:
    require(
        "check_public_business_action_execution.sh" in read(public_smoke_path),
        "public smoke missing business action execution check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_action_execution.sh"' in read(export_script_path),
        "export script missing business action execution checker",
    )
    require(
        "check_public_business_action_execution.sh" in read(ci_smoke_path),
        "private smoke missing business action execution checker",
    )
    require(
        "check_public_business_action_execution.sh" in read(release_gate_path),
        "release gate missing business action execution checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "public business action execution contract ok: "
    f"{len(plans)} execution plans, {len(preflight)} preflight checks, {len(dry_runs)} dry-run results"
)
PY
