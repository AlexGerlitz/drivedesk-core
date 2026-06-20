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


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
doc_path = root / "docs/public/REVIEW_CONSOLE.md"
evidence_path = root / "docs/public/evidence/review-console.sanitized.json"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
review_bundle_path = root / "docs/public/PUBLIC_REVIEW_BUNDLE.md"
review_bundle_json_path = root / "docs/public/evidence/public-review-bundle.sanitized.json"
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
docs_readme_path = root / "docs/public/README.md"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
checker_path = root / "scripts/check_public_review_console.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [demo_data_path, demo_app_path, demo_html_path, doc_path, evidence_path, checker_path]:
    require(path.is_file(), f"missing required review console file: {relative(path)}")

source = read(demo_data_path)
match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", source, flags=re.DOTALL)
require(match is not None, "demo-data.js payload assignment missing")
static_payload = json.loads(match.group(1)) if match else {}
api_payload = build_public_demo_payload()

static_review = static_payload.get("reviewConsole", {})
api_review = api_payload.get("reviewConsole", {})
require(static_review == api_review, "static and API reviewConsole payloads differ")
require(static_review.get("status") == "reviewable", "reviewConsole status mismatch")
require(len(static_review.get("summary", [])) == 4, "reviewConsole summary must have four cards")

for key in ["summary", "gates", "evidence", "handoff", "remainingWork", "boundary"]:
    require(isinstance(static_review.get(key), list) and static_review[key], f"reviewConsole missing non-empty {key}")

expected_gate_commands = {
    "bash scripts/run_public_review_bundle.sh",
    "bash scripts/check_public_review_console.sh",
    "bash scripts/public_repo_release_gate.sh",
    "bash scripts/check_public_provider_sandbox_dry_run.sh",
}
gate_commands = {
    gate.get("command")
    for gate in static_review.get("gates", [])
    if isinstance(gate, dict)
}
require(expected_gate_commands.issubset(gate_commands), "reviewConsole required gates missing")
for gate in static_review.get("gates", []):
    if isinstance(gate, dict):
        require(gate.get("status") == "passed", f"review gate is not passed: {gate.get('name')}")
        require(bool(gate.get("evidence")), f"review gate evidence missing: {gate.get('name')}")

expected_evidence_paths = {
    "docs/public/REVIEW_CONSOLE.md",
    "docs/public/PUBLIC_REVIEW_BUNDLE.md",
    "docs/public/evidence/public-evidence-index.sanitized.json",
    "docs/public/evidence/review-console.sanitized.json",
    "docs/public/PROVIDER_SANDBOX_DRY_RUN.md",
}
review_evidence_paths = {
    item.get("path")
    for item in static_review.get("evidence", [])
    if isinstance(item, dict)
}
require(expected_evidence_paths.issubset(review_evidence_paths), "reviewConsole evidence paths missing")
for item_path in expected_evidence_paths:
    require((root / item_path).exists(), f"reviewConsole evidence target missing: {item_path}")

openapi = build_app().openapi()
public_demo_schema = openapi.get("components", {}).get("schemas", {}).get("PublicDemoRead", {})
required_fields = set(public_demo_schema.get("required", []))
require("reviewConsole" in required_fields, "OpenAPI PublicDemoRead does not require reviewConsole")

html = read(demo_html_path)
for token in [
    'data-view="review"',
    'id="view-review"',
    'id="reviewTitle"',
    'id="reviewSummaryRows"',
    'id="reviewGateRows"',
    'id="reviewEvidenceRows"',
    'id="reviewHandoffRows"',
    'id="reviewRemainingRows"',
    'id="reviewBoundaryRows"',
    "Review Console",
]:
    require(token in html, f"public demo HTML missing {token}")

app = read(demo_app_path)
for token in [
    "payload.reviewConsole",
    "fillReviewConsole",
    "reviewConsole.summary",
    "reviewConsole.gates",
    "reviewConsole.evidence",
    "reviewConsole.handoff",
    "reviewConsole.remainingWork",
    "reviewConsole.boundary",
]:
    require(token in app, f"public demo app missing {token}")

doc = read(doc_path)
for token in [
    "Review Console",
    "GET /demo/public",
    "reviewConsole",
    "apps/admin/public-demo/",
    "bash scripts/check_public_review_console.sh",
    "bash scripts/run_public_review_bundle.sh",
    "synthetic data and sanitized evidence only",
]:
    require(token in doc, f"review console doc missing {token}")

evidence = json.loads(read(evidence_path) or "{}")
require(evidence.get("schema_version") == 1, "unexpected review console evidence schema version")
require(evidence.get("evidence_id") == "review_console", "unexpected review console evidence id")
require(evidence.get("status") == "validated", "unexpected review console evidence status")
require(evidence.get("demo_payload_key") == "reviewConsole", "unexpected review console payload key")
require(evidence.get("contract_check") == "bash scripts/check_public_review_console.sh", "unexpected review console contract check")
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
]:
    require(evidence.get("redaction", {}).get(key) is False, f"review console redaction flag must be false: {key}")

evidence_index = json.loads(read(evidence_index_json_path) or "{}")
entries = evidence_index.get("entries", [])
review_entries = [entry for entry in entries if entry.get("capability_id") == "review-console"]
require(len(review_entries) == 1, "evidence index must contain one review-console entry")
if review_entries:
    entry = review_entries[0]
    require(entry.get("public_doc") == "docs/public/REVIEW_CONSOLE.md", "review console index public_doc mismatch")
    require("docs/public/evidence/review-console.sanitized.json" in entry.get("evidence_files", []), "review console evidence missing from index")
    require("bash scripts/check_public_review_console.sh" in entry.get("verifiers", []), "review console verifier missing from index")

review_bundle = json.loads(read(review_bundle_json_path) or "{}")
require(
    "bash scripts/check_public_review_console.sh" in review_bundle.get("included_checks", []),
    "review bundle evidence missing review console check",
)
require(
    "docs/public/REVIEW_CONSOLE.md" in review_bundle.get("review_docs", []),
    "review bundle evidence missing review console doc",
)

for path, label in [
    (docs_readme_path, "docs/public README"),
    (review_bundle_path, "review bundle"),
    (quickstart_path, "quickstart"),
    (review_guide_path, "review guide"),
    (project_status_path, "project status"),
    (capability_map_path, "capability map"),
    (evidence_index_path, "evidence index"),
]:
    body = read(path)
    require("REVIEW_CONSOLE.md" in body, f"{label} missing REVIEW_CONSOLE.md")
    require("check_public_review_console.sh" in body, f"{label} missing review console checker")

export_script = read(export_script_path)
private_smoke = read(private_smoke_path)
release_gate = read(release_gate_path)
public_smoke = read(public_smoke_path)

if is_public_export:
    require("REVIEW_CONSOLE.md" in read(root_readme_path), "public README missing review console")
    require("REVIEW_CONSOLE.md" in read(index_html_path), "public Pages root missing review console")
    require("check_public_review_console.sh" in public_smoke, "public smoke missing review console check")
else:
    require("REVIEW_CONSOLE.md" in export_script, "export script missing review console doc")
    require("review-console.sanitized.json" in export_script, "export script missing review console evidence")
    require('copy_path "scripts/check_public_review_console.sh"' in export_script, "export script missing review console checker copy")
    require("check_public_review_console.sh" in private_smoke, "private smoke missing review console check")
    require("docs/public/REVIEW_CONSOLE.md" in release_gate, "release gate missing review console required file")
    require("docs/public/evidence/review-console.sanitized.json" in release_gate, "release gate missing review console evidence required file")
    require("scripts/check_public_review_console.sh" in release_gate, "release gate missing review console checker required file")
    require("check_public_review_console.sh" in release_gate, "release gate missing review console check")

serialized = json.dumps({"review": static_review, "evidence": evidence}, ensure_ascii=False, sort_keys=True)
private_patterns = [
    re.compile(r"auto\s*school\s*54", re.IGNORECASE),
    re.compile("auto" + "school54", re.IGNORECASE),
    re.compile("land" + "vps", re.IGNORECASE),
    re.compile("duck" + "dns", re.IGNORECASE),
    re.compile("xr" + "ay", re.IGNORECASE),
    re.compile("vl" + "ess", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
]
for pattern in private_patterns:
    require(not pattern.search(serialized), f"review console contains private marker: {pattern.pattern}")

if errors:
    print("public review console check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print("public review console check ok")
PY
