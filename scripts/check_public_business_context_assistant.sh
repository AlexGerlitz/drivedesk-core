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


doc_path = root / "docs/public/BUSINESS_CONTEXT_ASSISTANT.md"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
system_review_path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
roadmap_path = root / "docs/public/ROADMAP.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
openapi_path = root / "docs/openapi.json"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
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
    demo_data_path,
    demo_html_path,
    demo_app_path,
    openapi_path,
    schemas_path,
    main_path,
    sdk_generator_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
assistant = api_payload.get("businessContextAssistant", {})
static_assistant = static_payload.get("businessContextAssistant", {})

require(assistant == static_assistant, "API and static businessContextAssistant differ")
require(assistant.get("status") == "previewed", "businessContextAssistant status mismatch")
require(
    assistant.get("command") == "POST /tenants/{tenant_id}/business-workbench-context/preview",
    "businessContextAssistant command mismatch",
)
require(assistant.get("role") == "accountant", "businessContextAssistant role mismatch")
require(assistant.get("subject") == "deal:DEAL-2026-001", "businessContextAssistant subject mismatch")
require(
    {item.get("label") for item in assistant.get("summary", [])}
    >= {"Context cards", "Source systems", "Suggested actions", "External writes"},
    "businessContextAssistant summary missing required labels",
)

source_systems = set(assistant.get("sourceSystems", []))
require(
    source_systems
    == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
        "legal.reference.mock",
    },
    f"source systems mismatch: {sorted(source_systems)}",
)

cards = assistant.get("contextCards", [])
require(len(cards) == 4, "context card count mismatch")
require(
    {card.get("systemFamily") for card in cards}
    == {"crm", "bank", "accounting", "legal"},
    "context card system families mismatch",
)
for card in cards:
    require(card.get("status") in {"ready", "attention", "action_required", "documented"}, f"bad card status: {card}")
    require(card.get("externalFetch") is False, f"context card fetches externally: {card}")
    require(card.get("externalMutation") is False, f"context card mutates externally: {card}")
    require(card.get("containsPii") is False, f"context card contains PII: {card}")
    require(card.get("rawPayloadIncluded") is False, f"context card includes raw payload: {card}")
    require(card.get("evidence") == "business_workbench_context.previewed", f"context card evidence mismatch: {card}")

legal_cards = [card for card in cards if card.get("systemFamily") == "legal"]
require(legal_cards and legal_cards[0].get("fullTextIncluded") is False, "legal card must not include full text")

rules = assistant.get("insightRules", [])
require(
    {rule.get("rule") for rule in rules}
    == {"correlate_payment_evidence", "detect_accounting_export_gap", "attach_policy_reference"},
    "insight rules mismatch",
)
for rule in rules:
    require(rule.get("externalMutation") is False, f"insight rule mutates externally: {rule}")
    require(rule.get("evidence") == "business_workbench_context.previewed", f"insight rule evidence mismatch: {rule}")

actions = assistant.get("suggestedActions", [])
require(
    {action.get("action") for action in actions}
    == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "attach_policy_reference",
        "prepare_internal_notification",
    },
    "suggested actions mismatch",
)
require(
    {action.get("mode") for action in actions}
    >= {"operator_review", "approval_required", "internal_reference", "draft_only"},
    "suggested action modes mismatch",
)
for action in actions:
    require(action.get("externalMutation") is False, f"suggested action mutates externally: {action}")
    require(str(action.get("endpoint", "")), f"suggested action endpoint missing: {action}")

boundaries = assistant.get("dataBoundaries", [])
require(
    {item.get("name") for item in boundaries}
    == {"read_only_context_preview", "no_raw_provider_payload", "secret_boundary", "legal_reference_link_only"},
    "data boundaries mismatch",
)
boundary_by_name = {item.get("name"): item for item in boundaries if isinstance(item, dict)}
require(boundary_by_name["read_only_context_preview"].get("externalFetch") is False, "context preview fetch boundary mismatch")
require(boundary_by_name["read_only_context_preview"].get("externalMutation") is False, "context preview mutation boundary mismatch")
require(boundary_by_name["no_raw_provider_payload"].get("rawPayloadIncluded") is False, "raw payload boundary mismatch")
require(boundary_by_name["no_raw_provider_payload"].get("containsPii") is False, "PII boundary mismatch")
require(boundary_by_name["secret_boundary"].get("browserTokenStorage") is False, "browser token boundary mismatch")
require(boundary_by_name["legal_reference_link_only"].get("fullTextIncluded") is False, "legal text boundary mismatch")

require(
    assistant.get("api", {}).get("standalone") == "GET /demo/business-context-assistant",
    "standalone API link mismatch",
)
require(
    assistant.get("api", {}).get("preview") == "POST /tenants/{tenant_id}/business-workbench-context/preview",
    "preview API link mismatch",
)
require(
    {item.get("path") for item in assistant.get("docs", [])}
    >= {
        "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
    },
    "businessContextAssistant docs mismatch",
)

serialized = json.dumps(assistant, ensure_ascii=False, sort_keys=True).lower()
for blocked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization", "access_token"]:
    require(blocked not in serialized, f"businessContextAssistant leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-context-assistant" in paths, "OpenAPI missing context assistant demo endpoint")
require(
    "/tenants/{tenant_id}/business-workbench-context/preview" in paths,
    "OpenAPI missing workbench context preview endpoint",
)
require(
    paths.get("/demo/business-context-assistant", {}).get("get", {}).get("operationId")
    == "business_context_assistant_demo_demo_business_context_assistant_get",
    "context assistant demo operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require("BusinessContextAssistantDemoRead" in components, "OpenAPI missing BusinessContextAssistantDemoRead schema")
require(
    "businessContextAssistant"
    in components.get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessContextAssistant",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-context-assistant" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing context assistant demo",
)

html = read(demo_html_path)
for token in [
    "Context Assistant",
    "businessContextSummaryRows",
    "businessContextCardRows",
    "businessContextRuleRows",
    "businessContextActionRows",
    "businessContextBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessContextAssistant",
    "fillBusinessContextAssistant",
    "businessContextSummaryRows",
    "businessContextCardRows",
    "businessContextRuleRows",
    "businessContextActionRows",
    "businessContextBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

sdk_generator = read(sdk_generator_path)
for token in [
    "BUSINESS_CONTEXT_ASSISTANT_PATH",
    "business_context_assistant_operation",
    "BusinessContextAssistantDemoRead",
    "business_context_assistant",
]:
    require(token in sdk_generator, f"SDK generator missing {token}")

if sdk_manifest_path.is_file():
    manifest = json.loads(read(sdk_manifest_path))
    context_manifest = manifest.get("business_context_assistant", {})
    require(context_manifest.get("path") == "/demo/business-context-assistant", "SDK manifest context path mismatch")
    require(context_manifest.get("method") == "GET", "SDK manifest context method mismatch")
    require(
        context_manifest.get("operation_id")
        == "business_context_assistant_demo_demo_business_context_assistant_get",
        "SDK manifest context operation mismatch",
    )
    require("businessContextAssistant" in manifest.get("required_fields", []), "SDK manifest missing public field")

for path, label in [
    (doc_path, "context assistant doc"),
    (api_demo_doc_path, "API demo doc"),
    (capability_map_path, "capability map"),
    (status_path, "project status"),
    (docs_readme_path, "docs README"),
    (platform_tour_path, "platform tour"),
    (system_review_path, "system review path"),
    (roadmap_path, "roadmap"),
]:
    text = read(path)
    for token in [
        "Business Context Assistant",
        "GET /demo/business-context-assistant",
        "businessContextAssistant",
        "business-workbench-context/preview",
    ]:
        require(token in text, f"{label} missing {token}")

if is_public_export:
    public_smoke_text = read(public_smoke_path)
    require(
        "check_public_business_context_assistant.sh" in public_smoke_text,
        "public smoke missing context assistant check",
    )
else:
    export_script = read(export_script_path)
    ci_smoke = read(ci_smoke_path)
    release_gate = read(release_gate_path)
    require(
        'copy_path "scripts/check_public_business_context_assistant.sh"' in export_script,
        "export script missing context assistant checker copy",
    )
    require(
        "check_public_business_context_assistant.sh" in ci_smoke,
        "private smoke missing context assistant check",
    )
    require(
        "check_public_business_context_assistant.sh" in release_gate,
        "release gate missing context assistant check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_business_context_assistant.sh" in read(public_smoke_path),
        "public smoke missing context assistant check",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit("public business context assistant contract failed")

print(
    "public business context assistant contract ok: "
    f"{len(cards)} context cards, {len(rules)} rules, {len(actions)} suggested actions"
)
PY
