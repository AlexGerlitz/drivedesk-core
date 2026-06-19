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


doc_path = root / "docs/public/BUSINESS_APPROVAL_GATEWAY.md"
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
gateway = api_payload.get("businessApprovalGateway", {})
static_gateway = static_payload.get("businessApprovalGateway", {})

require(gateway == static_gateway, "API and static businessApprovalGateway differ")
require(gateway.get("status") == "previewed", "businessApprovalGateway status mismatch")
require(
    gateway.get("command") == "POST /tenants/{tenant_id}/business-approval-gateway/preview",
    "businessApprovalGateway command mismatch",
)
require(gateway.get("role") == "accountant", "businessApprovalGateway role mismatch")
require(gateway.get("subject") == "deal:DEAL-2026-001", "businessApprovalGateway subject mismatch")
require(
    {item.get("label") for item in gateway.get("summary", [])}
    >= {"Approval requests", "Policy checks", "Commit unlocks", "Provider writes"},
    "businessApprovalGateway summary missing required labels",
)

requests = gateway.get("approvalRequests", [])
require(len(requests) >= 1, "approval requests missing")
request_actions = {item.get("action") for item in requests if isinstance(item, dict)}
require(
    "queue_accounting_export_after_review" in request_actions,
    "approval request action missing",
)
for item in requests:
    require(item.get("status") == "approval_required", f"approval request status mismatch: {item}")
    require(item.get("requesterRole") == "accountant", f"approval requester role mismatch: {item}")
    require(item.get("approverRole") == "owner", f"approval approver role mismatch: {item}")
    require(
        str(item.get("idempotencyKey", "")).startswith("business-approval-gateway:"),
        f"approval idempotency key mismatch: {item}",
    )
    require(
        str(item.get("sourceIdempotencyKey", "")).startswith("business-action-execution:"),
        f"source idempotency key mismatch: {item}",
    )
    require(item.get("requiresDualControl") is True, f"dual control missing: {item}")
    require(item.get("commitWouldMutateProvider") is True, f"provider-changing candidate missing: {item}")
    require(item.get("externalMutation") is False, f"approval request mutates externally: {item}")
    require(item.get("containsPii") is False, f"approval request contains PII: {item}")
    require(item.get("rawPayloadIncluded") is False, f"approval request includes raw payload: {item}")
    require(item.get("evidence") == "business_approval_gateway.previewed", f"approval evidence mismatch: {item}")

policy_checks = gateway.get("policyChecks", [])
require(
    {item.get("check") for item in policy_checks}
    == {
        "rbac_approver_role",
        "dual_control_required",
        "idempotency_preserved",
        "provider_write_closed_until_approval",
    },
    "policy checks mismatch",
)
for item in policy_checks:
    require(item.get("externalMutation") is False, f"policy check mutates externally: {item}")
    require(item.get("evidence") == "business_approval_gateway.previewed", f"policy evidence mismatch: {item}")

routing = gateway.get("approverRouting", [])
require(
    {item.get("route") for item in routing}
    == {"owner_or_accountant_review", "escalate_if_sla_missed"},
    "approver routing mismatch",
)
for item in routing:
    require(item.get("externalDelivery") is False, f"approver route delivers externally: {item}")
    require(item.get("evidence") == "business_approval_gateway.previewed", f"routing evidence mismatch: {item}")

unlocks = gateway.get("commitUnlocks", [])
require(len(unlocks) >= 1, "commit unlocks missing")
for item in unlocks:
    require(item.get("wouldRecord") == "WorkflowActionRun", f"unlock record target mismatch: {item}")
    require(
        item.get("wouldEnqueueEvent") == "business.action.approval_granted",
        f"unlock event mismatch: {item}",
    )
    require(item.get("outboxReady") is True, f"unlock outbox readiness missing: {item}")
    require(item.get("providerWriteUnlocked") is False, f"provider write unlocked too early: {item}")
    require(item.get("externalMutation") is False, f"unlock mutates externally: {item}")
    require(item.get("rollbackAttached") is True, f"rollback attachment missing: {item}")
    require(item.get("evidence") == "business_approval_gateway.previewed", f"unlock evidence mismatch: {item}")

require(
    {item.get("event") for item in gateway.get("auditTrail", [])}
    == {
        "business_approval.requested",
        "business_approval.policy_checked",
        "business_approval.commit_unlocked",
    },
    "audit trail mismatch",
)
require(
    {item.get("name") for item in gateway.get("dataBoundaries", [])}
    == {
        "preview_only_no_approval_record",
        "provider_write_locked",
        "rbac_dual_control",
        "safe_approval_payload",
    },
    "data boundaries mismatch",
)

require(
    gateway.get("api", {}).get("standalone") == "GET /demo/business-approval-gateway",
    "standalone API link mismatch",
)
require(
    gateway.get("api", {}).get("preview") == "POST /tenants/{tenant_id}/business-approval-gateway/preview",
    "preview API link mismatch",
)
require(
    gateway.get("api", {}).get("actionExecution") == "POST /tenants/{tenant_id}/business-action-executions/preview",
    "action execution API link mismatch",
)
require(
    {item.get("path") for item in gateway.get("docs", [])}
    >= {
        "docs/public/BUSINESS_APPROVAL_GATEWAY.md",
        "docs/public/BUSINESS_ACTION_EXECUTION.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
    },
    "businessApprovalGateway docs mismatch",
)

serialized = json.dumps(gateway, ensure_ascii=False, sort_keys=True).lower()
for forbidden_token in [
    "never-return-this",
    "+70000000000",
    "synthetic customer",
    "password",
    "authorization",
    "access_token",
]:
    require(forbidden_token not in serialized, f"businessApprovalGateway leaked token: {forbidden_token}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-approval-gateway" in paths, "OpenAPI missing approval gateway demo endpoint")
require(
    "/tenants/{tenant_id}/business-approval-gateway/preview" in paths,
    "OpenAPI missing approval gateway preview endpoint",
)
require(
    paths.get("/demo/business-approval-gateway", {}).get("get", {}).get("operationId")
    == "business_approval_gateway_demo_demo_business_approval_gateway_get",
    "approval gateway demo operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require("BusinessApprovalGatewayDemoRead" in components, "OpenAPI missing BusinessApprovalGatewayDemoRead schema")
require("BusinessApprovalGatewayPreviewRead" in components, "OpenAPI missing BusinessApprovalGatewayPreviewRead schema")
require(
    "businessApprovalGateway"
    in components.get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessApprovalGateway",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-approval-gateway" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing approval gateway demo",
)
require(
    "/tenants/{tenant_id}/business-approval-gateway/preview" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing approval gateway preview",
)

html = read(demo_html_path)
for token in [
    "Approval Gateway",
    "businessApprovalGatewaySummaryRows",
    "businessApprovalGatewayRequestRows",
    "businessApprovalGatewayPolicyRows",
    "businessApprovalGatewayUnlockRows",
    "businessApprovalGatewayBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessApprovalGateway",
    "fillBusinessApprovalGateway",
    "businessApprovalGatewaySummaryRows",
    "businessApprovalGatewayRequestRows",
    "businessApprovalGatewayPolicyRows",
    "businessApprovalGatewayUnlockRows",
    "businessApprovalGatewayBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

sdk_generator = read(sdk_generator_path)
for token in [
    "BUSINESS_APPROVAL_GATEWAY_PATH",
    "business_approval_gateway_operation",
    "BusinessApprovalGatewayDemoRead",
    "business_approval_gateway",
]:
    require(token in sdk_generator, f"SDK generator missing {token}")

if sdk_manifest_path.is_file():
    manifest = json.loads(read(sdk_manifest_path))
    gateway_manifest = manifest.get("business_approval_gateway", {})
    require(gateway_manifest.get("path") == "/demo/business-approval-gateway", "SDK manifest gateway path mismatch")
    require(gateway_manifest.get("method") == "GET", "SDK manifest gateway method mismatch")
    require(
        gateway_manifest.get("operation_id")
        == "business_approval_gateway_demo_demo_business_approval_gateway_get",
        "SDK manifest gateway operation mismatch",
    )
    require(
        "businessApprovalGateway" in manifest.get("required_fields", []),
        "SDK manifest public demo required fields missing gateway",
    )

for path, name in [
    (doc_path, "business approval gateway doc"),
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
    require("BUSINESS_APPROVAL_GATEWAY.md" in text, f"{name} missing approval gateway doc link")
    require("businessApprovalGateway" in text, f"{name} missing businessApprovalGateway token")
    require("GET /demo/business-approval-gateway" in text, f"{name} missing standalone endpoint")

require("/demo/business-approval-gateway" in read(main_path), "API main missing approval gateway demo route")
require("/business-approval-gateway/preview" in read(main_path), "API main missing approval gateway preview route")
require("preview_business_approval_gateway" in read(services_path), "services missing approval gateway implementation")
require("BusinessApprovalGatewayPreviewRead" in read(schemas_path), "schemas missing BusinessApprovalGatewayPreviewRead")

if is_public_export:
    require(
        "check_public_business_approval_gateway.sh" in read(public_smoke_path),
        "public smoke missing business approval gateway check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_approval_gateway.sh"' in read(export_script_path),
        "export script missing business approval gateway checker",
    )
    require(
        "check_public_business_approval_gateway.sh" in read(ci_smoke_path),
        "private smoke missing business approval gateway checker",
    )
    require(
        "check_public_business_approval_gateway.sh" in read(release_gate_path),
        "release gate missing business approval gateway checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "public business approval gateway contract ok: "
    f"{len(requests)} approval requests, {len(policy_checks)} policy checks, {len(unlocks)} commit unlocks"
)
PY
