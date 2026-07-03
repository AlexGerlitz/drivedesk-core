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


doc_path = root / "docs/public/BUSINESS_INTAKE_API_HANDOFF.md"
pipeline_doc_path = root / "docs/public/BUSINESS_INTAKE_PIPELINE.md"
handoff_doc_path = root / "docs/public/BUSINESS_TASK_HANDOFF.md"
api_doc_path = root / "docs/public/API_BACKED_DEMO.md"
client_doc_path = root / "docs/public/CLIENT_SDK.md"
docs_readme_path = root / "docs/public/README.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
openapi_path = root / "docs/openapi.json"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_image_path = root / "docs/public/assets/drivedesk-core-demo-overview.png"
api_test_path = root / "tests/test_drivedesk_core_api.py"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [
    doc_path,
    pipeline_doc_path,
    handoff_doc_path,
    api_doc_path,
    client_doc_path,
    docs_readme_path,
    status_path,
    capability_map_path,
    evidence_index_path,
    evidence_json_path,
    openapi_path,
    demo_html_path,
    demo_data_path,
    demo_image_path,
    api_test_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

doc_text = read(doc_path)
for token in [
    "Business Intake API Handoff",
    "60-Second Review",
    "Telegram-style intake",
    "FastAPI preview endpoint",
    "validated business record shape",
    "admin workbench queue",
    "status transition",
    "outbox/integration handoff",
    "pytest/API smoke/CI",
    "GET /demo/business-intake-pipeline",
    "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
    "GET /demo/business-task-handoff",
    "docs/openapi.json",
    "sdk/generated/public-demo/",
    "tests/test_drivedesk_core_api.py",
    "apps/admin/public-demo/index.html",
    "docs/public/assets/drivedesk-core-demo-overview.png",
    "bash scripts/check_public_business_intake_api_handoff.sh",
    "bash scripts/check_public_demo_sdk.sh",
    "no real names",
    "no phone numbers",
    "no Telegram or chat IDs",
    "no admin URLs",
    "no raw provider payloads",
    "no logs, dumps, hostnames, tokens, or credentials",
]:
    require(token in doc_text, f"handoff doc missing {token}")

blocked_patterns = [
    re.compile(r"\+?\d[\d ()-]{8,}\d"),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile("auto" + "school54", re.IGNORECASE),
    re.compile("duck" + "dns", re.IGNORECASE),
    re.compile("xr" + "ay", re.IGNORECASE),
    re.compile("vl" + "ess", re.IGNORECASE),
    re.compile(r"/opt/", re.IGNORECASE),
]
for pattern in blocked_patterns:
    require(not pattern.search(doc_text), f"handoff doc contains private marker: {pattern.pattern}")

payload = build_public_demo_payload()
require("businessIntakePipeline" in payload, "public payload missing businessIntakePipeline")
require("businessTaskHandoff" in payload, "public payload missing businessTaskHandoff")
require(payload["businessIntakePipeline"].get("status") == "previewed", "intake pipeline status mismatch")
require(payload["businessTaskHandoff"].get("status") == "previewed", "task handoff status mismatch")
require(
    payload["businessIntakePipeline"].get("command")
    == "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
    "intake pipeline preview command mismatch",
)
require(
    payload["businessTaskHandoff"].get("command")
    == "POST /tenants/{tenant_id}/business-task-handoffs/preview",
    "task handoff preview command mismatch",
)

serialized_payload = json.dumps(
    {
        "businessIntakePipeline": payload["businessIntakePipeline"],
        "businessTaskHandoff": payload["businessTaskHandoff"],
    },
    ensure_ascii=False,
    sort_keys=True,
).lower()
for blocked in ["password", "authorization", "telegram_chat", "real customer"]:
    require(blocked not in serialized_payload, f"public payload leaked marker: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
runtime_openapi = build_app().openapi()
for source_name, schema in [("committed", openapi), ("runtime", runtime_openapi)]:
    paths = schema.get("paths", {})
    for route in [
        "/demo/business-intake-pipeline",
        "/tenants/{tenant_id}/business-intake-pipeline/preview",
        "/demo/business-task-handoff",
        "/tenants/{tenant_id}/business-task-handoffs/preview",
    ]:
        require(route in paths, f"{source_name} OpenAPI missing {route}")

for text_path in [
    docs_readme_path,
    status_path,
    capability_map_path,
    evidence_index_path,
]:
    text = read(text_path)
    require("BUSINESS_INTAKE_API_HANDOFF.md" in text, f"{text_path.relative_to(root)} missing handoff doc")
    require(
        "check_public_business_intake_api_handoff.sh" in text,
        f"{text_path.relative_to(root)} missing handoff checker",
    )

index_payload = json.loads(read(evidence_json_path) or "{}")
entries = index_payload.get("entries", [])
entry = next((item for item in entries if item.get("capability_id") == "business-intake-api-handoff"), None)
require(entry is not None, "evidence index missing business-intake-api-handoff")
if entry:
    require(entry.get("public_doc") == "docs/public/BUSINESS_INTAKE_API_HANDOFF.md", "handoff entry public_doc mismatch")
    require(
        "bash scripts/check_public_business_intake_api_handoff.sh" in entry.get("verifiers", []),
        "handoff entry verifier missing",
    )
    require(entry.get("status") == "validated", "handoff entry status mismatch")
    require("synthetic" in entry.get("boundary", "").lower(), "handoff entry boundary must be synthetic")

for token in [
    "businessIntakePipeline",
    "businessTaskHandoff",
    "businessIntakeSummaryRows",
    "businessTaskSummaryRows",
]:
    require(token in read(demo_html_path) or token in read(demo_data_path), f"demo surface missing {token}")

for token in [
    "test_business_intake_pipeline",
    "test_business_task_handoff",
]:
    require(token in read(api_test_path), f"API tests missing {token}")

if is_public_export:
    require("BUSINESS_INTAKE_API_HANDOFF.md" in read(root / "README.md"), "public README missing handoff route")
    require("BUSINESS_INTAKE_API_HANDOFF.md" in read(root / "index.html"), "public Pages root missing handoff route")
    require(
        "check_public_business_intake_api_handoff.sh" in read(public_smoke_path),
        "public smoke missing handoff checker",
    )
else:
    require(
        'copy_path "scripts/check_public_business_intake_api_handoff.sh"' in read(export_script_path),
        "export script missing handoff checker copy",
    )
    require("BUSINESS_INTAKE_API_HANDOFF.md" in read(export_script_path), "export script missing handoff doc")
    require(
        "check_public_business_intake_api_handoff.sh" in read(private_smoke_path),
        "private smoke missing handoff checker",
    )
    require(
        "check_public_business_intake_api_handoff.sh" in read(release_gate_path),
        "release gate missing handoff checker",
    )

if errors:
    print("public business intake API handoff check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    sys.exit(1)

print("public business intake API handoff check ok")
PY
