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

"$PYTHON_BIN" - <<'PY' "$ROOT"
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
doc_path = root / "docs/public/INTEGRATION_REPAIR.md"
evidence_path = root / "docs/public/evidence/integration-repair.sanitized.json"
demo_api_path = root / "apps/api/drivedesk_api/demo.py"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
openapi_path = root / "docs/openapi.json"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
sdk_python_path = root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py"
sdk_javascript_path = root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs"
sdk_typescript_path = root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
api_docs_path = root / "docs/public/API_BACKED_DEMO.md"
client_sdk_path = root / "docs/public/CLIENT_SDK.md"
export_script_path = root / "scripts/export_public_repo.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
manifest_path = root / "PUBLIC_EXPORT_MANIFEST.md"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
is_public_export = manifest_path.is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(doc_path.is_file(), "missing docs/public/INTEGRATION_REPAIR.md")
require(evidence_path.is_file(), "missing integration repair evidence JSON")

doc = read(doc_path)
for token in [
    "Integration Repair Workbench",
    "GET /demo/integration-repair",
    "integrationRepair",
    "incidentMatrix",
    "repairRunbooks",
    "impactAnalysis",
    "repairActions",
    "safeExecutionPlan",
    "providerCallEnabled=false",
    "externalMutation=false",
    "rawPayloadIncluded=false",
    "containsPii=false",
    "bash scripts/check_public_integration_repair.sh",
]:
    require(token in doc, f"integration repair doc missing {token}")

evidence = json.loads(read(evidence_path) or "{}")
require(evidence.get("schema_version") == 1, "unexpected integration repair evidence schema")
require(evidence.get("artifact_id") == "drivedesk-core-integration-repair", "unexpected integration repair evidence id")
require(evidence.get("status") == "previewed", "unexpected integration repair evidence status")
require(evidence.get("repair_level") == "operator_repair_ready", "unexpected integration repair level")
require(evidence.get("verifier") == "bash scripts/check_public_integration_repair.sh", "integration repair verifier mismatch")
for source in ["outbox_event:retry", "outbox_event:dead_letter", "reconciliation:mismatched"]:
    require(source in evidence.get("incident_sources", []), f"integration repair evidence missing source: {source}")
for key in [
    "integration.retry_backlog",
    "integration.dead_letter",
    "integration.reconciliation_mismatch",
]:
    require(key in evidence.get("runbook_keys", []), f"integration repair evidence missing runbook: {key}")
for step in [
    "classify_failure",
    "attach_business_impact",
    "prepare_safe_actions",
    "dry_run_first",
    "approval_before_commit",
    "observe_after_repair",
]:
    require(step in evidence.get("safe_execution_steps", []), f"integration repair evidence missing step: {step}")
for action in [
    "run_connection_diagnostics",
    "retry_after_diagnostics",
    "fix_mapping_profile",
    "open_reconciliation_review",
]:
    require(action in evidence.get("repair_actions", []), f"integration repair evidence missing action: {action}")
for key in [
    "provider_call_enabled",
    "external_mutation",
    "raw_payload_included",
    "contains_pii",
    "automatic_provider_retry",
    "public_demo_persistence",
]:
    require(evidence.get("safety_assertions", {}).get(key) is False, f"integration repair safety assertion must be false: {key}")
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
]:
    require(evidence.get("redaction", {}).get(key) is False, f"integration repair redaction flag must be false: {key}")

sys.path.insert(0, str(root / "apps/api"))
sys.path.insert(0, str(root / "apps/worker"))
sys.path.insert(0, str(root / "packages/core"))
from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

demo = build_public_demo_payload()
repair = demo.get("integrationRepair", {})
require(isinstance(repair, dict), "public demo missing integrationRepair")
require(repair.get("status") == "previewed", "integrationRepair status mismatch")
require(repair.get("command") == "GET /demo/integration-repair", "integrationRepair command mismatch")
require(repair.get("repairLevel") == "operator_repair_ready", "integrationRepair level mismatch")
require(repair.get("incidentCount") == 3, "integrationRepair incident count mismatch")
require(repair.get("criticalCount") == 2, "integrationRepair critical count mismatch")
require(repair.get("safeActionCount") == 1, "integrationRepair safe action count mismatch")
require(
    {item.get("label") for item in repair.get("summary", []) if isinstance(item, dict)}
    >= {"Incidents", "Critical", "Safe actions", "Provider writes"},
    "integrationRepair summary labels incomplete",
)
incidents = repair.get("incidentMatrix", [])
require(len(incidents) == 3, "integrationRepair incident matrix length mismatch")
require(
    {f"{item.get('sourceType')}:{item.get('sourceStatus')}" for item in incidents if isinstance(item, dict)}
    == {"outbox_event:retry", "outbox_event:dead_letter", "reconciliation:mismatched"},
    "integrationRepair incident sources mismatch",
)
require(
    {item.get("adapterKey") for item in incidents if isinstance(item, dict)}
    >= {"accounting.export.mock", "crm.bitrix24.mock"},
    "integrationRepair adapter keys incomplete",
)
require(
    {item.get("providerCallEnabled") for item in incidents if isinstance(item, dict)} == {False},
    "integrationRepair incidents must not call providers",
)
require(
    {item.get("externalMutation") for item in incidents if isinstance(item, dict)} == {False},
    "integrationRepair incidents must not mutate providers",
)
runbooks = repair.get("repairRunbooks", [])
require(
    {item.get("runbookKey") for item in runbooks if isinstance(item, dict)}
    == {
        "integration.retry_backlog",
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
    },
    "integrationRepair runbooks mismatch",
)
require(
    {item.get("severity") for item in runbooks if isinstance(item, dict)} >= {"warning", "critical"},
    "integrationRepair runbook severities incomplete",
)
impact = repair.get("impactAnalysis", [])
require(
    {item.get("area") for item in impact if isinstance(item, dict)}
    == {"workflow_delivery", "financial_reconciliation", "operator_queue"},
    "integrationRepair impact areas mismatch",
)
actions = repair.get("repairActions", [])
require(
    {item.get("action") for item in actions if isinstance(item, dict)}
    == {
        "run_connection_diagnostics",
        "retry_after_diagnostics",
        "fix_mapping_profile",
        "open_reconciliation_review",
    },
    "integrationRepair actions mismatch",
)
require(
    [item.get("action") for item in actions if isinstance(item, dict) and item.get("safeToAutoRun") is True]
    == ["run_connection_diagnostics"],
    "integrationRepair safe auto-run action mismatch",
)
require(
    {item.get("providerCallEnabled") for item in actions if isinstance(item, dict)} == {False},
    "integrationRepair actions must not call providers",
)
require(
    {item.get("externalMutation") for item in actions if isinstance(item, dict)} == {False},
    "integrationRepair actions must not mutate providers",
)
plan = repair.get("safeExecutionPlan", [])
require(
    {item.get("step") for item in plan if isinstance(item, dict)}
    == {
        "classify_failure",
        "attach_business_impact",
        "prepare_safe_actions",
        "dry_run_first",
        "approval_before_commit",
        "observe_after_repair",
    },
    "integrationRepair safe execution plan mismatch",
)
boundaries = repair.get("dataBoundaries", [])
require(
    {item.get("name") for item in boundaries if isinstance(item, dict)}
    == {
        "repair_preview_only",
        "safe_payload_summary",
        "approval_before_retry",
        "private_provider_boundary",
    },
    "integrationRepair data boundaries mismatch",
)
for field in ("externalMutation", "providerCallEnabled", "rawPayloadIncluded", "containsPii"):
    require(
        {item.get(field) for item in boundaries if isinstance(item, dict)} == {False},
        f"integrationRepair boundary field must be false: {field}",
    )
require(repair.get("api", {}).get("standalone") == "GET /demo/integration-repair", "integrationRepair standalone API mismatch")

openapi_live = build_app().openapi()
require("/demo/integration-repair" in openapi_live.get("paths", {}), "live OpenAPI missing integration repair endpoint")
required_fields = (
    openapi_live.get("components", {})
    .get("schemas", {})
    .get("PublicDemoRead", {})
    .get("required", [])
)
require("integrationRepair" in required_fields, "PublicDemoRead missing integrationRepair")
require("IntegrationRepairDemoRead" in openapi_live.get("components", {}).get("schemas", {}), "OpenAPI missing IntegrationRepairDemoRead")

for path, label, tokens in [
    (
        demo_api_path,
        "demo API",
        ["integrationRepair", "_public_integration_repair", "GET /demo/integration-repair"],
    ),
    (
        schemas_path,
        "schemas",
        ["IntegrationRepairDemoRead", "integrationRepair"],
    ),
    (
        main_path,
        "main API",
        ["/demo/integration-repair", "IntegrationRepairDemoRead"],
    ),
    (
        demo_app_path,
        "public demo app",
        ["integrationRepair", "fillIntegrationRepair", "integrationRepairIncidentRows"],
    ),
    (
        demo_html_path,
        "public demo HTML",
        ["Integration Repair", "integrationRepairSummaryRows", "integrationRepairActionRows"],
    ),
    (
        openapi_path,
        "committed OpenAPI",
        ["/demo/integration-repair", "IntegrationRepairDemoRead", "integrationRepair"],
    ),
    (
        sdk_manifest_path,
        "SDK manifest",
        ["integration_repair", "/demo/integration-repair", "IntegrationRepairDemoRead"],
    ),
    (
        sdk_python_path,
        "Python SDK",
        ["INTEGRATION_REPAIR_PATH", "get_integration_repair", "validate_integration_repair_payload"],
    ),
    (
        sdk_javascript_path,
        "JavaScript SDK",
        ["INTEGRATION_REPAIR_PATH", "getIntegrationRepair", "validateIntegrationRepairPayload"],
    ),
    (
        sdk_typescript_path,
        "TypeScript SDK",
        ["IntegrationRepairPayload", "getIntegrationRepair"],
    ),
    (
        status_path,
        "project status",
        ["Integration repair", "GET /demo/integration-repair", "integrationRepair"],
    ),
    (
        roadmap_path,
        "roadmap",
        ["Public-safe integration repair workbench", "GET /demo/integration-repair"],
    ),
    (
        capability_path,
        "capability map",
        ["Integration repair", "docs/public/INTEGRATION_REPAIR.md"],
    ),
    (
        api_docs_path,
        "API docs",
        ["/demo/integration-repair", "integrationRepair"],
    ),
    (
        client_sdk_path,
        "client SDK docs",
        ["get_integration_repair", "IntegrationRepairPayload"],
    ),
]:
    text = read(path)
    for token in tokens:
        require(token in text, f"{label} missing {token}")

if not is_public_export:
    for path, label, tokens in [
        (
            export_script_path,
            "export script",
            [
                "docs/public/INTEGRATION_REPAIR.md",
                "docs/public/evidence/integration-repair.sanitized.json",
                "scripts/check_public_integration_repair.sh",
            ],
        ),
        (
            release_gate_path,
            "release gate",
            ["check_public_integration_repair.sh", "INTEGRATION_REPAIR.md"],
        ),
        (
            private_smoke_path,
            "private smoke",
            ["check_public_integration_repair.sh"],
        ),
    ]:
        text = read(path)
        for token in tokens:
            require(token in text, f"{label} missing {token}")

if public_smoke_path.is_file():
    require("check_public_integration_repair.sh" in read(public_smoke_path), "public smoke missing integration repair check")

if is_public_export:
    for path, label, tokens in [
        (root_readme_path, "public root README", ["INTEGRATION_REPAIR.md", "Integration Repair"]),
        (index_html_path, "public root index", ["INTEGRATION_REPAIR.md", "Integration repair"]),
        (manifest_path, "public manifest", ["INTEGRATION_REPAIR.md", "integration-repair.sanitized.json"]),
    ]:
        text = read(path)
        for token in tokens:
            require(token in text, f"{label} missing {token}")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public integration repair check ok")
PY
