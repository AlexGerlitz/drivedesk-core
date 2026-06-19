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


doc_path = root / "docs/public/BUSINESS_SCENARIO_REPLAY.md"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
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
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [
    doc_path,
    api_demo_doc_path,
    capability_map_path,
    status_path,
    docs_readme_path,
    platform_tour_path,
    demo_data_path,
    demo_html_path,
    demo_app_path,
    openapi_path,
    schemas_path,
    main_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
replay = api_payload.get("businessScenarioReplay", {})
static_replay = static_payload.get("businessScenarioReplay", {})

require(replay == static_replay, "API and static businessScenarioReplay differ")
require(replay.get("status") == "validated", "businessScenarioReplay status mismatch")
require(
    replay.get("command") == "bash scripts/check_public_business_scenario_replay.sh",
    "businessScenarioReplay verifier mismatch",
)
require(
    {item.get("label") for item in replay.get("summary", [])}
    >= {"Scenario groups", "Source systems", "Operator actions", "External writes"},
    "businessScenarioReplay summary missing required labels",
)
scenarios = {item.get("id"): item for item in replay.get("scenarios", [])}
require(
    set(scenarios) == {
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    },
    "businessScenarioReplay scenario ids mismatch",
)
require(
    {item.get("stage") for item in replay.get("flow", [])}
    == {"signal", "normalize", "detect", "plan", "execute"},
    "businessScenarioReplay flow mismatch",
)
require(
    {item.get("path") for item in replay.get("docs", [])}
    >= {
        "docs/public/BUSINESS_SCENARIO_REPLAY.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/API_BACKED_DEMO.md",
        "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    },
    "businessScenarioReplay docs mismatch",
)

for scenario_id, scenario in scenarios.items():
    require(scenario.get("sourceSystems"), f"{scenario_id} source systems missing")
    require(scenario.get("normalizedFacts"), f"{scenario_id} normalized facts missing")
    require(scenario.get("recommendedActions"), f"{scenario_id} recommended actions missing")
    require(scenario.get("automationCandidates"), f"{scenario_id} automation candidates missing")
    require(scenario.get("evidence"), f"{scenario_id} evidence missing")
    require(scenario.get("dataBoundary"), f"{scenario_id} data boundary missing")
    require(
        any(item.get("safeToAutoRun") is False for item in scenario.get("automationCandidates", [])),
        f"{scenario_id} missing approval-gated automation candidate",
    )
    serialized = json.dumps(scenario, sort_keys=True).lower()
    for blocked in ["access_token", "secret", "password", "+7", "phone=", "full_name"]:
        require(blocked not in serialized, f"{scenario_id} leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-scenario-replay" in paths, "OpenAPI missing business scenario replay endpoint")
require(
    paths.get("/demo/business-scenario-replay", {}).get("get", {}).get("operationId")
    == "business_scenario_replay_demo_demo_business_scenario_replay_get",
    "business scenario replay operation id mismatch",
)
require(
    "BusinessScenarioReplayRead" in openapi.get("components", {}).get("schemas", {}),
    "OpenAPI missing BusinessScenarioReplayRead schema",
)
require(
    "businessScenarioReplay"
    in openapi.get("components", {}).get("schemas", {}).get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessScenarioReplay",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-scenario-replay" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing business scenario replay endpoint",
)

html = read(demo_html_path)
for token in [
    "Business Scenario Replay",
    "businessScenarioSummaryRows",
    "businessScenarioRows",
    "businessScenarioFlowRows",
    "businessScenarioDocRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessScenarioReplay",
    "fillBusinessScenarioReplay",
    "businessScenarioSummaryRows",
    "businessScenarioRows",
    "businessScenarioFlowRows",
    "businessScenarioDocRows",
]:
    require(token in app_js, f"public demo app missing {token}")

for path, name in [
    (doc_path, "business scenario replay doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (docs_readme_path, "public docs README"),
    (platform_tour_path, "platform tour"),
]:
    text = read(path)
    require("BUSINESS_SCENARIO_REPLAY.md" in text, f"{name} missing scenario replay doc link")
    require("businessScenarioReplay" in text, f"{name} missing businessScenarioReplay token")

require(
    "/demo/business-scenario-replay" in read(main_path),
    "API main missing business scenario replay route",
)
require(
    "BusinessScenarioReplayRead" in read(schemas_path),
    "schemas missing BusinessScenarioReplayRead",
)

if is_public_export:
    require(
        "check_public_business_scenario_replay.sh" in read(public_smoke_path),
        "public smoke missing business scenario replay check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_scenario_replay.sh"' in read(export_script_path),
        "export script missing business scenario replay checker",
    )
    require(
        "check_public_business_scenario_replay.sh" in read(ci_smoke_path),
        "private smoke missing business scenario replay checker",
    )
    require(
        "check_public_business_scenario_replay.sh" in read(release_gate_path),
        "release gate missing business scenario replay checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public business scenario replay check ok")
PY
