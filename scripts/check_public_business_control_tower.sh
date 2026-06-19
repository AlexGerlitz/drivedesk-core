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

export PYTHONPATH="$ROOT/apps/api:$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"
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


doc_path = root / "docs/public/BUSINESS_CONTROL_TOWER.md"
adr_path = root / "docs/adr/0064-business-operations-control-tower.md"
briefing_adr_path = root / "docs/adr/0065-business-role-briefings.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
export_script_path = root / "scripts/export_public_repo.sh"
ci_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [doc_path, adr_path, briefing_adr_path, demo_data_path, demo_html_path, demo_app_path]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
control = api_payload.get("businessControlTower", {})

require(bool(control), "API demo missing businessControlTower")
require(
    {item.get("label") for item in control.get("summary", [])}
    >= {"Observed systems", "Open exceptions", "Repair actions", "External writes"},
    "businessControlTower summary missing required cards",
)
briefing = control.get("briefing", {})
require(briefing.get("role") == "accountant", "businessControlTower briefing role mismatch")
require(briefing.get("riskLevel") == "attention", "businessControlTower briefing risk mismatch")
require(
    set(briefing.get("sourceSystems", []))
    >= {"crm.bitrix24.mock", "bank.statement.mock", "accounting.export.mock"},
    "businessControlTower briefing missing source systems",
)
require(
    {item.get("type") for item in briefing.get("highlights", [])}
    >= {"business_exception", "state_observation", "repair_context"},
    "businessControlTower briefing highlights missing",
)
require(
    {item.get("action") for item in briefing.get("recommendedActions", [])}
    >= {"execute_repair_dry_run", "review_accounting_export"},
    "businessControlTower briefing recommended actions missing",
)
require(
    briefing.get("api", {}).get("preview") == "POST /tenants/{tenant_id}/business-briefings/preview",
    "businessControlTower briefing preview endpoint missing",
)
require(
    {item.get("system") for item in control.get("observations", [])}
    >= {"crm.bitrix24.mock", "bank.statement.mock", "accounting.export.mock"},
    "businessControlTower observations missing systems",
)
require(
    {item.get("type") for item in control.get("exceptions", [])} == {"crm_payment_mismatch"},
    "businessControlTower exception mismatch",
)
require(
    {item.get("action") for item in control.get("repairActions", [])} == {"sync_status"},
    "businessControlTower repair action mismatch",
)
require(
    {item.get("externalMutation") for item in control.get("repairActions", [])} == {False},
    "businessControlTower repair action must be public-safe",
)
require(
    set(control.get("metrics", []))
    >= {"drivedesk_business_state_observations", "drivedesk_business_exceptions", "drivedesk_repair_actions"},
    "businessControlTower metrics missing",
)

demo_source = read(demo_data_path)
match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", demo_source, flags=re.DOTALL)
require(match is not None, "static demo payload missing")
static_payload = json.loads(match.group(1)) if match else {}
require(
    static_payload.get("businessControlTower") == control,
    "static and API businessControlTower payloads differ",
)

openapi = build_app().openapi()
paths = set(openapi.get("paths", {}))
required_paths = {
    "/tenants/{tenant_id}/business-briefings/preview",
    "/tenants/{tenant_id}/business-state/observations",
    "/tenants/{tenant_id}/business-exceptions",
    "/tenants/{tenant_id}/business-exceptions/{business_exception_id}/status",
    "/tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
    "/tenants/{tenant_id}/repair-actions",
    "/tenants/{tenant_id}/repair-actions/{repair_action_id}/approve",
    "/tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
}
require(required_paths.issubset(paths), "OpenAPI missing business control paths")

doc_text = read(doc_path)
for needle in [
    "Business Operations Control Tower",
    "POST /tenants/{tenant_id}/business-briefings/preview",
    "POST /tenants/{tenant_id}/business-state/observations",
    "BusinessBriefing",
    "BusinessStateObservation",
    "BusinessException",
    "RepairAction",
    "drivedesk_business_exceptions",
]:
    require(needle in doc_text, f"business control tower doc missing {needle}")

html = read(demo_html_path)
for needle in [
    'data-view="control"',
    'id="controlTowerSummaryRows"',
    'id="controlTowerBriefingRows"',
    'id="controlTowerBriefingActionRows"',
    'id="controlTowerObservationRows"',
    'id="controlTowerExceptionRows"',
    'id="controlTowerRepairRows"',
]:
    require(needle in html, f"demo HTML missing {needle}")

app_js = read(demo_app_path)
for needle in [
    "businessControlTower",
    "controlTowerBriefingRows",
    "fillBusinessControlTower",
    "controlTowerSummaryRows",
]:
    require(needle in app_js, f"demo app missing {needle}")

if is_public_export:
    require(
        "check_public_business_control_tower.sh" in read(public_smoke_path),
        "public smoke missing business control checker",
    )
else:
    require(
        'copy_path "docs/adr/0064-business-operations-control-tower.md"' in read(export_script_path),
        "export script missing ADR 0064",
    )
    require(
        'copy_path "docs/adr/0065-business-role-briefings.md"' in read(export_script_path),
        "export script missing ADR 0065",
    )
    require(
        'copy_path "scripts/check_public_business_control_tower.sh"' in read(export_script_path),
        "export script missing business control checker",
    )
    require(
        "check_public_business_control_tower.sh" in read(ci_smoke_path),
        "private smoke missing business control checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public business control tower check ok")
PY
