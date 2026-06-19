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


doc_path = root / "docs/public/BUSINESS_TASK_HANDOFF.md"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
system_review_path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
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
    system_review_path,
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
handoff = api_payload.get("businessTaskHandoff", {})
static_handoff = static_payload.get("businessTaskHandoff", {})

require(handoff == static_handoff, "API and static businessTaskHandoff differ")
require(handoff.get("status") == "previewed", "businessTaskHandoff status mismatch")
require(
    handoff.get("command") == "POST /tenants/{tenant_id}/business-task-handoffs/preview",
    "businessTaskHandoff command mismatch",
)
require(
    {item.get("label") for item in handoff.get("summary", [])}
    >= {"Task cards", "Internal outbox", "Draft notifications", "External writes"},
    "businessTaskHandoff summary missing required labels",
)
require(handoff.get("role") == "accountant", "businessTaskHandoff role mismatch")
require(handoff.get("subject") == "deal:DEAL-2026-001", "businessTaskHandoff subject mismatch")
require(len(handoff.get("taskCards", [])) == 2, "businessTaskHandoff task count mismatch")
require(len(handoff.get("outboxCandidates", [])) == 2, "businessTaskHandoff outbox candidate count mismatch")
require(len(handoff.get("notificationDrafts", [])) == 2, "businessTaskHandoff draft count mismatch")

for card in handoff.get("taskCards", []):
    require(card.get("status") == "would_create", "task card must be preview-only")
    require(card.get("wouldCreate") == "BusinessRecord(type=task)", "task card target mismatch")
    require(card.get("externalMutation") is False, "task card mutates externally")
    require(card.get("containsPii") is False, "task card contains PII")
    require(card.get("rawPayloadIncluded") is False, "task card includes raw payload")
    require(card.get("evidence") == "business_task_handoff.previewed", "task card evidence mismatch")

for candidate in handoff.get("outboxCandidates", []):
    require(candidate.get("eventType") == "task.created", "outbox candidate event mismatch")
    require(candidate.get("adapterKey") == "internal.noop", "outbox candidate adapter mismatch")
    require(candidate.get("status") == "would_enqueue", "outbox candidate must be preview-only")
    require(candidate.get("payloadProfile") == "safe_task_reference", "outbox candidate payload profile mismatch")
    require(candidate.get("containsPii") is False, "outbox candidate contains PII")
    require(candidate.get("externalMutation") is False, "outbox candidate mutates externally")

for draft in handoff.get("notificationDrafts", []):
    require(draft.get("status") == "draft_only", "notification draft status mismatch")
    require(draft.get("externalDelivery") is False, "notification draft sends externally")
    require(draft.get("containsPii") is False, "notification draft contains PII")
    require(draft.get("requiresSecret") is False, "notification draft requires secret")

require(
    {item.get("gate") for item in handoff.get("approvalGates", [])}
    == {"task_creation_review", "external_write_gate", "repair_action_approval"},
    "businessTaskHandoff approval gates mismatch",
)
require(
    {item.get("name") for item in handoff.get("dataBoundaries", [])}
    == {"preview_only_no_persistence", "internal_only_outbox", "safe_task_payload"},
    "businessTaskHandoff data boundaries mismatch",
)
require(
    {item.get("path") for item in handoff.get("docs", [])}
    >= {
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/WORKFLOW_DEMO.md",
        "docs/public/BUSINESS_INTAKE_PIPELINE.md",
    },
    "businessTaskHandoff docs mismatch",
)

serialized = json.dumps(handoff, ensure_ascii=False, sort_keys=True).lower()
for blocked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization"]:
    require(blocked not in serialized, f"businessTaskHandoff leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-task-handoff" in paths, "OpenAPI missing business task handoff demo endpoint")
require(
    "/tenants/{tenant_id}/business-task-handoffs/preview" in paths,
    "OpenAPI missing business task handoff preview endpoint",
)
require(
    paths.get("/demo/business-task-handoff", {}).get("get", {}).get("operationId")
    == "business_task_handoff_demo_demo_business_task_handoff_get",
    "business task handoff demo operation id mismatch",
)
require(
    "BusinessTaskHandoffDemoRead" in openapi.get("components", {}).get("schemas", {}),
    "OpenAPI missing BusinessTaskHandoffDemoRead schema",
)
require(
    "BusinessTaskHandoffPreviewRead" in openapi.get("components", {}).get("schemas", {}),
    "OpenAPI missing BusinessTaskHandoffPreviewRead schema",
)
require(
    "businessTaskHandoff"
    in openapi.get("components", {}).get("schemas", {}).get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessTaskHandoff",
)

app_openapi = build_app().openapi()
require("/demo/business-task-handoff" in app_openapi.get("paths", {}), "runtime OpenAPI missing handoff demo")
require(
    "/tenants/{tenant_id}/business-task-handoffs/preview" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing handoff preview",
)

html = read(demo_html_path)
for token in [
    "Business Task Handoff",
    "businessTaskSummaryRows",
    "businessTaskRows",
    "businessTaskOutboxRows",
    "businessTaskDraftRows",
    "businessTaskBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessTaskHandoff",
    "fillBusinessTaskHandoff",
    "businessTaskSummaryRows",
    "businessTaskRows",
    "businessTaskOutboxRows",
    "businessTaskDraftRows",
    "businessTaskBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

for path, name in [
    (doc_path, "business task handoff doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (docs_readme_path, "public docs README"),
    (platform_tour_path, "platform tour"),
    (system_review_path, "system review path"),
]:
    text = read(path)
    require("BUSINESS_TASK_HANDOFF.md" in text, f"{name} missing handoff doc link")
    require("businessTaskHandoff" in text, f"{name} missing businessTaskHandoff token")

require("/demo/business-task-handoff" in read(main_path), "API main missing handoff demo route")
require("/business-task-handoffs/preview" in read(main_path), "API main missing handoff preview route")
require("preview_business_task_handoff" in read(services_path), "services missing handoff implementation")
require("BusinessTaskHandoffPreviewRead" in read(schemas_path), "schemas missing BusinessTaskHandoffPreviewRead")

if is_public_export:
    require(
        "check_public_business_task_handoff.sh" in read(public_smoke_path),
        "public smoke missing business task handoff check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_task_handoff.sh"' in read(export_script_path),
        "export script missing business task handoff checker",
    )
    require(
        "check_public_business_task_handoff.sh" in read(ci_smoke_path),
        "private smoke missing business task handoff checker",
    )
    require(
        "check_public_business_task_handoff.sh" in read(release_gate_path),
        "release gate missing business task handoff checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public business task handoff check ok")
PY
