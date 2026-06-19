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


doc_path = root / "docs/public/BUSINESS_INTAKE_PIPELINE.md"
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
services_path = root / "apps/api/drivedesk_api/services.py"
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
    services_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
pipeline = api_payload.get("businessIntakePipeline", {})
static_pipeline = static_payload.get("businessIntakePipeline", {})

require(pipeline == static_pipeline, "API and static businessIntakePipeline differ")
require(pipeline.get("status") == "previewed", "businessIntakePipeline status mismatch")
require(
    pipeline.get("command") == "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
    "businessIntakePipeline command mismatch",
)
require(
    {item.get("label") for item in pipeline.get("summary", [])}
    >= {"Provider events", "Dropped unsafe keys", "Detected exceptions", "External writes"},
    "businessIntakePipeline summary missing required labels",
)
require(
    pipeline.get("sourceSystems") == [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    ],
    "businessIntakePipeline source systems mismatch",
)
require(len(pipeline.get("intakePreviews", [])) == 3, "businessIntakePipeline intake preview count mismatch")
require(
    {item.get("providerKey") for item in pipeline.get("intakePreviews", [])}
    == {"crm.bitrix24.mock", "bank.statement.mock", "accounting.export.mock"},
    "businessIntakePipeline provider keys mismatch",
)
workbench = pipeline.get("workbench", {})
require(
    {item.get("systemFamily") for item in workbench.get("contextCards", [])}
    == {"crm", "bank", "accounting"},
    "businessIntakePipeline workbench cards mismatch",
)
for card in workbench.get("contextCards", []):
    require(card.get("rawPayloadIncluded") is False, "workbench card includes raw payload")
    require(card.get("piiIncluded") is False, "workbench card includes PII")
    require(card.get("externalMutation") is False, "workbench card mutates external system")

detections = pipeline.get("detections", {})
require(detections.get("status") == "detected", "businessIntakePipeline detection status mismatch")
require(
    detections.get("detectedExceptions", [{}])[0].get("exceptionType") == "crm_payment_mismatch",
    "businessIntakePipeline missing crm_payment_mismatch",
)
require(
    detections.get("suggestedRepairActions", [{}])[0].get("requiresApproval") is True,
    "businessIntakePipeline repair candidate must require approval",
)
require(
    detections.get("suggestedRepairActions", [{}])[0].get("externalMutation") is False,
    "businessIntakePipeline repair candidate must not mutate externally",
)
require(
    {item.get("gate") for item in pipeline.get("actionPlan", {}).get("approvalGates", [])}
    == {"external_write_gate", "notification_delivery_gate"},
    "businessIntakePipeline approval gates mismatch",
)
require(pipeline.get("notifications", {}).get("externalDelivery") is False, "pipeline notification delivery enabled")
require(pipeline.get("notifications", {}).get("containsPii") is False, "pipeline notification contains PII")
require(
    {item.get("name") for item in pipeline.get("dataBoundaries", [])}
    == {"no_external_calls", "no_persistence", "secret_and_pii_boundary"},
    "businessIntakePipeline data boundaries mismatch",
)
require(
    {item.get("path") for item in pipeline.get("docs", [])}
    >= {
        "docs/public/BUSINESS_INTAKE_PIPELINE.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/API_BACKED_DEMO.md",
    },
    "businessIntakePipeline docs mismatch",
)

serialized = json.dumps(pipeline, ensure_ascii=False, sort_keys=True).lower()
for blocked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization"]:
    require(blocked not in serialized, f"businessIntakePipeline leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-intake-pipeline" in paths, "OpenAPI missing business intake demo endpoint")
require(
    "/tenants/{tenant_id}/business-intake-pipeline/preview" in paths,
    "OpenAPI missing business intake pipeline preview endpoint",
)
require(
    paths.get("/demo/business-intake-pipeline", {}).get("get", {}).get("operationId")
    == "business_intake_pipeline_demo_demo_business_intake_pipeline_get",
    "business intake demo operation id mismatch",
)
require(
    "BusinessIntakePipelineDemoRead" in openapi.get("components", {}).get("schemas", {}),
    "OpenAPI missing BusinessIntakePipelineDemoRead schema",
)
require(
    "BusinessIntakePipelinePreviewRead" in openapi.get("components", {}).get("schemas", {}),
    "OpenAPI missing BusinessIntakePipelinePreviewRead schema",
)
require(
    "businessIntakePipeline"
    in openapi.get("components", {}).get("schemas", {}).get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessIntakePipeline",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-intake-pipeline" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing business intake demo endpoint",
)
require(
    "/tenants/{tenant_id}/business-intake-pipeline/preview" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing business intake pipeline preview endpoint",
)

html = read(demo_html_path)
for token in [
    "Business Intake Pipeline",
    "businessIntakeSummaryRows",
    "businessIntakeRows",
    "businessIntakeWorkbenchRows",
    "businessIntakeActionRows",
    "businessIntakeBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessIntakePipeline",
    "fillBusinessIntakePipeline",
    "businessIntakeSummaryRows",
    "businessIntakeRows",
    "businessIntakeWorkbenchRows",
    "businessIntakeActionRows",
    "businessIntakeBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

for path, name in [
    (doc_path, "business intake pipeline doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (docs_readme_path, "public docs README"),
    (platform_tour_path, "platform tour"),
]:
    text = read(path)
    require("BUSINESS_INTAKE_PIPELINE.md" in text, f"{name} missing pipeline doc link")
    require("businessIntakePipeline" in text, f"{name} missing businessIntakePipeline token")

require(
    "/demo/business-intake-pipeline" in read(main_path),
    "API main missing business intake pipeline demo route",
)
require(
    "/business-intake-pipeline/preview" in read(main_path),
    "API main missing business intake pipeline preview route",
)
require(
    "preview_business_intake_pipeline" in read(services_path),
    "services missing business intake pipeline implementation",
)
require(
    "BusinessIntakePipelinePreviewRead" in read(schemas_path),
    "schemas missing BusinessIntakePipelinePreviewRead",
)

if is_public_export:
    require(
        "check_public_business_intake_pipeline.sh" in read(public_smoke_path),
        "public smoke missing business intake pipeline check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_intake_pipeline.sh"' in read(export_script_path),
        "export script missing business intake pipeline checker",
    )
    require(
        "check_public_business_intake_pipeline.sh" in read(ci_smoke_path),
        "private smoke missing business intake pipeline checker",
    )
    require(
        "check_public_business_intake_pipeline.sh" in read(release_gate_path),
        "release gate missing business intake pipeline checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public business intake pipeline check ok")
PY
