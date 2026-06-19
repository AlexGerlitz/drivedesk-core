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


doc_path = root / "docs/public/INTEGRATION_RUNTIME.md"
api_doc_path = root / "docs/public/API_BACKED_DEMO.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
readme_path = root / "docs/public/README.md"
roadmap_path = root / "docs/public/ROADMAP.md"
client_sdk_path = root / "docs/public/CLIENT_SDK.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
system_review_path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
openapi_path = root / "docs/openapi.json"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
services_path = root / "apps/api/drivedesk_api/services.py"
adapters_path = root / "packages/core/drivedesk_core/adapters.py"
sdk_generator_path = root / "scripts/generate_public_demo_sdk.py"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"

for path in [
    doc_path,
    api_doc_path,
    status_path,
    readme_path,
    roadmap_path,
    client_sdk_path,
    capability_map_path,
    platform_tour_path,
    system_review_path,
    demo_data_path,
    demo_html_path,
    demo_app_path,
    openapi_path,
    schemas_path,
    main_path,
    services_path,
    adapters_path,
    sdk_generator_path,
    sdk_manifest_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
runtime = api_payload.get("integrationRuntime", {})
static_runtime = static_payload.get("integrationRuntime", {})

require(runtime == static_runtime, "API and static integrationRuntime differ")
require(runtime.get("status") == "previewed", "integrationRuntime status mismatch")
require(
    runtime.get("command") == "POST /tenants/{tenant_id}/integration-runtime/preview",
    "integrationRuntime command mismatch",
)
require(runtime.get("adapterKey") == "accounting.export.mock", "runtime adapter mismatch")
require(runtime.get("operationKey") == "accounting_export_execute", "runtime operation mismatch")
require(runtime.get("executionMode") == "contract_only", "runtime execution mode mismatch")
require(
    {item.get("label") for item in runtime.get("summary", [])}
    >= {"Runtime steps", "Adapter", "Outbox", "Provider calls"},
    "runtime summary missing required labels",
)

contract = runtime.get("operationContract", {})
require(contract.get("eventType") == "accounting.export.requested", "operation event mismatch")
require(contract.get("requiredConnectionScope") == "accounting:export", "operation scope mismatch")
require(contract.get("retryable") is True, "operation retryable mismatch")
require(contract.get("deadLetter") is True, "operation deadLetter mismatch")
require(contract.get("operatorReview") is True, "operation operatorReview mismatch")
require(
    set(contract.get("idempotencyKeys", [])) == {"tenant_id", "export_batch_id", "documents_hash"},
    "operation idempotency keys mismatch",
)

runtime_steps = runtime.get("runtimeSteps", [])
require(len(runtime_steps) >= 7, "runtime steps missing")
require(
    {item.get("step") for item in runtime_steps}
    >= {
        "contract_selected",
        "scope_preflight",
        "idempotency_prepared",
        "approval_dependency",
        "outbox_handoff",
        "worker_boundary",
        "reconciliation_plan",
    },
    "runtime step names mismatch",
)
require(
    {item.get("evidence") for item in runtime_steps}
    >= {
        "adapter_runtime.contract_selected",
        "adapter_runtime.scope_checked",
        "adapter_runtime.outbox_handoff_prepared",
        "adapter_runtime.worker_boundary_selected",
        "adapter_runtime.reconciliation_planned",
    },
    "runtime step evidence mismatch",
)

preflight = runtime.get("preflightChecks", [])
require(
    {item.get("check") for item in preflight}
    == {
        "adapter_registered",
        "operation_contract_present",
        "required_scope_available",
        "idempotency_keys_declared",
        "secret_boundary_server_side",
        "provider_write_disabled_in_preview",
    },
    "runtime preflight checks mismatch",
)
for item in preflight:
    require(item.get("externalMutation") is False, f"preflight mutates externally: {item}")
    require(item.get("evidence") == "adapter_runtime.previewed", f"preflight evidence mismatch: {item}")

outbox = runtime.get("outboxHandoff", {})
require(outbox.get("status") == "ready", "outbox handoff status mismatch")
require(outbox.get("wouldEnqueueEvent") == "accounting.export.requested", "outbox event mismatch")
require(outbox.get("requiredConnectionScope") == "accounting:export", "outbox scope mismatch")
require(outbox.get("providerCallEnabled") is False, "outbox provider call enabled")
require(outbox.get("externalMutation") is False, "outbox mutates externally")

worker = runtime.get("workerBoundary", {})
require(worker.get("status") == "ready", "worker boundary status mismatch")
require(worker.get("publicRunMode") == "contract_only", "worker public mode mismatch")
require(worker.get("providerCallEnabled") is False, "worker provider call enabled")
require(worker.get("externalMutation") is False, "worker mutates externally")
require(worker.get("rawPayloadIncluded") is False, "worker includes raw payload")
require(worker.get("containsPii") is False, "worker includes pii")

reconciliation = runtime.get("reconciliationPlan", [])
require(
    {item.get("step") for item in reconciliation}
    >= {"capture_expected_result", "compare_provider_evidence", "route_mismatch_to_operator"},
    "reconciliation plan mismatch",
)
for item in reconciliation:
    require(item.get("externalMutation") is False, f"reconciliation mutates externally: {item}")

incident_routes = runtime.get("incidentRoutes", [])
require(
    {item.get("route") for item in incident_routes}
    == {"retry_queue", "dead_letter_review", "reconciliation_mismatch"},
    "incident routes mismatch",
)
for item in incident_routes:
    require(item.get("externalMutation") is False, f"incident route mutates externally: {item}")

require(
    {item.get("name") for item in runtime.get("dataBoundaries", [])}
    == {
        "contract_only_preview",
        "server_side_secret_boundary",
        "safe_payload_boundary",
        "approval_before_provider_write",
    },
    "runtime data boundaries mismatch",
)

require(runtime.get("api", {}).get("standalone") == "GET /demo/integration-runtime", "standalone API mismatch")
require(
    runtime.get("api", {}).get("preview") == "POST /tenants/{tenant_id}/integration-runtime/preview",
    "preview API mismatch",
)
require(
    {item.get("path") for item in runtime.get("docs", [])}
    >= {
        "docs/public/INTEGRATION_RUNTIME.md",
        "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
        "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
    },
    "integrationRuntime docs mismatch",
)

serialized = json.dumps(runtime, ensure_ascii=False, sort_keys=True).lower()
for forbidden_token in [
    "never-return-this",
    "+70000000000",
    "synthetic customer",
    "password",
    "authorization",
    "access_token",
    "refresh_token",
]:
    require(forbidden_token not in serialized, f"integrationRuntime leaked token: {forbidden_token}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/integration-runtime" in paths, "OpenAPI missing runtime demo endpoint")
require("/tenants/{tenant_id}/integration-runtime/preview" in paths, "OpenAPI missing runtime preview endpoint")
require(
    paths.get("/demo/integration-runtime", {}).get("get", {}).get("operationId")
    == "integration_runtime_demo_demo_integration_runtime_get",
    "runtime demo operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require("IntegrationRuntimeDemoRead" in components, "OpenAPI missing IntegrationRuntimeDemoRead")
require("IntegrationRuntimePreviewRead" in components, "OpenAPI missing IntegrationRuntimePreviewRead")
require("integrationRuntime" in components.get("PublicDemoRead", {}).get("required", []), "PublicDemoRead missing integrationRuntime")

app_openapi = build_app().openapi()
require(app_openapi["paths"].keys() >= paths.keys(), "committed OpenAPI has path not produced by app")

html = read(demo_html_path)
for token in [
    "integrationRuntimeSummaryRows",
    "integrationRuntimeStepRows",
    "integrationRuntimePreflightRows",
    "integrationRuntimeOutboxRows",
    "integrationRuntimeBoundaryRows",
]:
    require(token in html, f"missing runtime UI id: {token}")

app_js = read(demo_app_path)
for token in [
    "fillIntegrationRuntime",
    "integrationRuntime",
    "runtimeSteps",
    "preflightChecks",
    "outboxHandoff",
    "workerBoundary",
    "incidentRoutes",
]:
    require(token in app_js, f"missing runtime app token: {token}")

manifest = json.loads(read(sdk_manifest_path) or "{}")
runtime_manifest = manifest.get("integration_runtime", {})
require(runtime_manifest.get("path") == "/demo/integration-runtime", "SDK manifest runtime path mismatch")
require(runtime_manifest.get("method") == "GET", "SDK manifest runtime method mismatch")
require(
    runtime_manifest.get("operation_id") == "integration_runtime_demo_demo_integration_runtime_get",
    "SDK manifest runtime operation id mismatch",
)
require(
    runtime_manifest.get("required_fields")
    == [
        "status",
        "command",
        "summary",
        "adapterKey",
        "operationKey",
        "executionMode",
        "operationContract",
        "runtimeSteps",
        "preflightChecks",
        "outboxHandoff",
        "workerBoundary",
        "reconciliationPlan",
        "incidentRoutes",
        "dataBoundaries",
        "api",
        "docs",
    ],
    "SDK manifest runtime required fields mismatch",
)
require("integrationRuntime" in manifest.get("required_fields", []), "SDK required fields missing integrationRuntime")

for path, tokens in {
    doc_path: [
        "GET /demo/integration-runtime",
        "POST /tenants/{tenant_id}/integration-runtime/preview",
        "adapter_runtime.previewed",
        "accounting.export.mock",
    ],
    api_doc_path: ["/demo/integration-runtime", "integrationRuntime"],
    status_path: ["Integration runtime", "scripts/check_public_integration_runtime.sh"],
    readme_path: ["Integration runtime", "INTEGRATION_RUNTIME.md"],
    roadmap_path: ["Integration Runtime", "adapter runtime"],
    client_sdk_path: ["integration_runtime", "/demo/integration-runtime"],
    capability_map_path: ["Integration Runtime", "INTEGRATION_RUNTIME.md"],
    platform_tour_path: ["Integration Runtime", "adapter_runtime.previewed"],
    system_review_path: ["Integration runtime", "check_public_integration_runtime.sh"],
    sdk_generator_path: ["INTEGRATION_RUNTIME_PATH", "integration_runtime_required_fields"],
    services_path: ["preview_integration_runtime", "build_adapter_runtime_plan"],
    adapters_path: ["build_adapter_runtime_plan", "adapter_runtime.previewed"],
}.items():
    content = read(path)
    for token in tokens:
        require(token in content, f"{path.relative_to(root)} missing token: {token}")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "public integration runtime contract ok: "
    f"{len(runtime_steps)} runtime steps, {len(preflight)} preflight checks, "
    f"{len(incident_routes)} incident routes"
)
PY
