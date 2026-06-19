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
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
contract_path = root / "infra/observability/observability-dashboard.sanitized.json"
evidence_path = root / "docs/public/evidence/observability-dashboard.sanitized.json"
doc_path = root / "docs/public/OBSERVABILITY_DASHBOARD.md"
adr_path = root / "docs/adr/0076-public-safe-observability-dashboard.md"
demo_path = root / "apps/api/drivedesk_api/demo.py"
main_path = root / "apps/api/drivedesk_api/main.py"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
openapi_path = root / "docs/openapi.json"
html_path = root / "apps/admin/public-demo/index.html"
js_path = root / "apps/admin/public-demo/app.js"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
roadmap_path = root / "docs/public/ROADMAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
docs_readme_path = root / "docs/public/README.md"
root_readme_path = root / "README.md"
index_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"

errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        errors.append(f"missing json file: {path.relative_to(root)}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


contract = load_json(contract_path)
evidence = load_json(evidence_path)
require(contract == evidence, "observability dashboard contract and public evidence differ")

require(contract.get("schema_version") == 1, "schema_version mismatch")
require(contract.get("check") == "public_observability_dashboard", "check mismatch")
require(contract.get("dashboard_model") == "grafana_style_dashboard_contract", "dashboard model mismatch")
require(contract.get("data_profile") == "synthetic_demo_data", "data profile mismatch")

dashboard_groups = contract.get("dashboard_groups", [])
panel_catalog = contract.get("panel_catalog", [])
require(isinstance(dashboard_groups, list) and len(dashboard_groups) >= 4, "dashboard groups missing")
require(isinstance(panel_catalog, list) and len(panel_catalog) >= 6, "panel catalog missing")

group_keys = {item.get("key") for item in dashboard_groups if isinstance(item, dict)}
require(
    {"api_runtime", "integration_health", "business_workflow", "security_auth"}.issubset(group_keys),
    f"dashboard groups incomplete: {sorted(group_keys)}",
)

panel_keys = {item.get("key") for item in panel_catalog if isinstance(item, dict)}
require(
    {"request_rate", "latency_p95", "error_ratio", "outbox_backlog", "dead_letters", "structured_logs"}.issubset(panel_keys),
    f"panel catalog incomplete: {sorted(panel_keys)}",
)

datasources = {item.get("datasource") for item in panel_catalog if isinstance(item, dict)}
require({"prometheus", "loki"}.issubset(datasources), f"datasources incomplete: {sorted(datasources)}")

for group in dashboard_groups:
    if not isinstance(group, dict):
        errors.append("dashboard group must be object")
        continue
    runbook = str(group.get("runbook", ""))
    require(runbook.startswith("docs/public/"), f"group runbook is not public doc: {runbook}")
    require((root / runbook).is_file(), f"group runbook target missing: {runbook}")
    require(isinstance(group.get("panels"), list) and group["panels"], f"group panels missing: {group.get('key')}")

for panel in panel_catalog:
    if not isinstance(panel, dict):
        errors.append("panel must be object")
        continue
    labels = set(panel.get("safe_labels", []))
    forbidden_labels = {"email", "user_id", "tenant_id", "token", "phone", "name", "payload", "request_body"}
    require(labels.isdisjoint(forbidden_labels), f"unsafe panel labels on {panel.get('key')}")
    query = str(panel.get("query", ""))
    require(query, f"panel query missing: {panel.get('key')}")
    require("password" not in query.lower(), f"unsafe query token in {panel.get('key')}")
    require(panel.get("alert_link"), f"panel alert link missing: {panel.get('key')}")

checks = contract.get("checks", {}) if isinstance(contract.get("checks"), dict) else {}
for check in [
    "dashboard_groups_present",
    "panel_catalog_present",
    "prometheus_queries_present",
    "loki_queries_present",
    "alerts_link_to_runbooks",
    "safe_labels_only",
    "public_demo_payload_present",
    "openapi_path_present",
    "public_docs_linked",
    "private_markers_absent",
]:
    require(checks.get(check) is True, f"observability dashboard check failed: {check}")
require(checks.get("production_data_touched") is False, "observability dashboard touches production data")

redaction = contract.get("redaction", {}) if isinstance(contract.get("redaction"), dict) else {}
for key in [
    "paths_included",
    "hostnames_included",
    "addresses_included",
    "credentials_included",
    "raw_logs_included",
    "request_bodies_included",
    "production_data_included",
]:
    require(redaction.get(key) is False, f"redaction flag not false: {key}")

doc = read(doc_path)
for token in [
    "Observability Dashboard",
    "GET /demo/observability-dashboard",
    "docs/public/evidence/observability-dashboard.sanitized.json",
    "infra/observability/observability-dashboard.sanitized.json",
    "bash scripts/check_public_observability_dashboard.sh",
    "Dashboard Groups",
    "Panel Contract",
    "No raw payloads or PII",
]:
    require(token in doc, f"observability dashboard doc missing {token}")

adr = read(adr_path)
for token in [
    "ADR-0076",
    "Public-Safe Observability Dashboard Contract",
    "GET /demo/observability-dashboard",
    "scripts/check_public_observability_dashboard.sh",
]:
    require(token in adr, f"observability dashboard ADR missing {token}")

demo = read(demo_path)
for token in [
    "_public_observability_dashboard",
    "observabilityDashboard",
    "GET /demo/observability-dashboard",
    "dashboard_contract_ready",
    "observability_dashboard.panel.latency_p95",
]:
    require(token in demo, f"demo payload missing {token}")

main = read(main_path)
for token in [
    "ObservabilityDashboardDemoRead",
    "/demo/observability-dashboard",
    "observabilityDashboard",
]:
    require(token in main, f"API route missing {token}")

schemas = read(schemas_path)
for token in [
    "class ObservabilityDashboardDemoRead",
    "observabilityDashboard",
    "dashboardGroups",
    "panelCatalog",
]:
    require(token in schemas, f"schema missing {token}")

if openapi_path.is_file():
    openapi = load_json(openapi_path)
    paths = openapi.get("paths", {}) if isinstance(openapi.get("paths"), dict) else {}
    require("/demo/observability-dashboard" in paths, "OpenAPI missing /demo/observability-dashboard")
    components = openapi.get("components", {}) if isinstance(openapi.get("components"), dict) else {}
    schemas_obj = components.get("schemas", {}) if isinstance(components.get("schemas"), dict) else {}
    require("ObservabilityDashboardDemoRead" in schemas_obj, "OpenAPI missing ObservabilityDashboardDemoRead")

html = read(html_path)
for token in [
    "observabilityDashboardSummaryRows",
    "observabilityDashboardGroupRows",
    "observabilityDashboardPanelRows",
    "observabilityDashboardQueryRows",
    "observabilityDashboardBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

js = read(js_path)
for token in [
    "payload.observabilityDashboard",
    "function fillObservabilityDashboard",
    "fillObservabilityDashboard();",
    "dashboard.panelCatalog",
]:
    require(token in js, f"public demo JS missing {token}")

if demo_data_path.is_file():
    demo_data = read(demo_data_path)
    require("observabilityDashboard" in demo_data, "demo-data missing observabilityDashboard")
    require("observability_dashboard.panel.latency_p95" in demo_data, "demo-data missing dashboard panel evidence")

for path, label in [
    (project_status_path, "project status"),
    (capability_map_path, "technical capability map"),
    (roadmap_path, "roadmap"),
    (evidence_index_path, "evidence index"),
    (docs_readme_path, "docs public README"),
]:
    content = read(path)
    require("OBSERVABILITY_DASHBOARD.md" in content, f"{label} missing OBSERVABILITY_DASHBOARD.md")
    require("check_public_observability_dashboard.sh" in content, f"{label} missing checker")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    require("OBSERVABILITY_DASHBOARD.md" in read(root_readme_path), "public README missing observability dashboard")
    require("OBSERVABILITY_DASHBOARD.md" in read(index_path), "public Pages root missing observability dashboard")
    require(
        "check_public_observability_dashboard.sh" in read(public_smoke_path),
        "public smoke missing observability dashboard check",
    )
else:
    export_script = read(export_script_path)
    for token in [
        'copy_path "infra/observability"',
        "OBSERVABILITY_DASHBOARD.md",
        'copy_path "scripts/check_public_observability_dashboard.sh"',
        "0076-public-safe-observability-dashboard.md",
        "observability-dashboard.sanitized.json",
    ]:
        require(token in export_script, f"export script missing {token}")
    require(
        "check_public_observability_dashboard.sh" in read(private_smoke_path),
        "private smoke missing observability dashboard check",
    )
    require(
        "check_public_observability_dashboard.sh" in read(release_gate_path),
        "release gate missing observability dashboard check",
    )

private_patterns = [
    r"auto\s*" + r"school\s*54",
    "auto" + "school54",
    "land" + "vps",
    "duck" + "dns",
    "215" + "689",
    "185" + r"\.80\.",
    "152" + r"\.53\.",
    "2a0a:",
    "/" + "opt/",
    "xr" + "ay",
]
scan_text = "\n".join(
    [
        json.dumps(contract, sort_keys=True),
        doc,
        adr,
    ]
).lower()
for pattern in private_patterns:
    require(re.search(pattern, scan_text) is None, f"private marker leaked into dashboard: {pattern}")

if errors:
    for error in errors:
        print(f"observability_dashboard_error={error}", file=sys.stderr)
    raise SystemExit("public observability dashboard check failed")

print(
    "public observability dashboard check ok: "
    f"groups={len(dashboard_groups)} panels={len(panel_catalog)}"
)
PY
