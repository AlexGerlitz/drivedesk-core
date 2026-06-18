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
path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
docs_readme_path = root / "docs/public/README.md"
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
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


def read(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8") if file_path.is_file() else ""


require(path.is_file(), "missing docs/public/SYSTEM_REVIEW_PATH.md")
text = read(path)

for token in [
    "System Review Path",
    "3-Minute Route",
    "Evidence Chain",
    "Verification Commands",
    "What This Proves",
    "Boundary",
    "GitHub Pages engineering reference",
    "apps/admin/public-demo/",
    "Workflow, Operations, Incidents, and Proof",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/EVIDENCE_INDEX.md",
    "docs/public/evidence/public-evidence-index.sanitized.json",
    "docs/public/SYSTEM_DESIGN.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/openapi.json",
    "GET /demo/public",
    "sdk/generated/public-demo/",
    "endToEndScenario",
    "approval -> notification -> adapter -> incident -> recovery -> proof",
    "architecture -> demo -> API -> SDK -> workflow -> observability -> incident -> release safety -> GitOps/IaC -> evidence index",
    "bash scripts/check_public_system_review_path.sh",
    "bash scripts/check_public_pages_entrypoint.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/ci_smoke_public.sh",
]:
    require(token in text, f"system review path missing {token}")

for target in [
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/EVIDENCE_INDEX.md",
    "docs/public/evidence/public-evidence-index.sanitized.json",
    "docs/public/SYSTEM_DESIGN.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
]:
    require((root / target).is_file(), f"system review target missing: {target}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (quickstart_path, "quickstart"),
    (review_guide_path, "review guide"),
    (project_status_path, "project status"),
    (capability_map_path, "capability map"),
    (evidence_index_path, "evidence index"),
]:
    doc = read(doc_path)
    require("SYSTEM_REVIEW_PATH.md" in doc, f"{label} missing SYSTEM_REVIEW_PATH.md")

if evidence_json_path.is_file():
    payload = json.loads(read(evidence_json_path))
    serialized = json.dumps(payload, sort_keys=True)
    require("docs/public/SYSTEM_REVIEW_PATH.md" in serialized, "evidence JSON missing system review path")
    require(
        "bash scripts/check_public_system_review_path.sh" in serialized,
        "evidence JSON missing system review verifier",
    )

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for target in [
        "README.md",
        "index.html",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_system_review_path.sh",
    ]:
        require((root / target).is_file(), f"public export target missing: {target}")
    require("SYSTEM_REVIEW_PATH.md" in read(root_readme_path), "public README missing system review path")
    require("SYSTEM_REVIEW_PATH.md" in read(index_path), "public Pages root missing system review path")
    require(
        "check_public_system_review_path.sh" in read(public_smoke_path),
        "public smoke missing system review path check",
    )
else:
    export_script = read(export_script_path)
    require("SYSTEM_REVIEW_PATH.md" in export_script, "export script missing system review path")
    require(
        'copy_path "scripts/check_public_system_review_path.sh"' in export_script,
        "export script missing system review checker copy",
    )
    require(
        "check_public_system_review_path.sh" in read(private_smoke_path),
        "private smoke missing system review path check",
    )
    require(
        "check_public_system_review_path.sh" in read(release_gate_path),
        "release gate missing system review path check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_system_review_path.sh" in read(public_smoke_path),
        "public smoke missing system review path check",
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
lowered = text.lower()
for pattern in private_patterns:
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into system review path: {pattern}")

if errors:
    for error in errors:
        print(f"system_review_path_error={error}", file=sys.stderr)
    raise SystemExit("public system review path check failed")

print("public system review path check ok: docs/public/SYSTEM_REVIEW_PATH.md")
PY
