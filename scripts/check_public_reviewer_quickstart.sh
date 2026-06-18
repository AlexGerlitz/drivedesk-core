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

import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
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


require(quickstart_path.is_file(), "missing docs/public/REVIEWER_QUICKSTART.md")
text = read(quickstart_path)

for token in [
    "Verification Quickstart",
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "5-Minute Pass",
    "15-Minute Verification",
    "45-Minute Deep Check",
    "Pass criteria",
    "Boundary",
    "GitHub Pages engineering reference",
    "Public demo Workflow, Operations, Incidents, and Proof tabs",
    "end-to-end scenario",
    "approval -> notification -> adapter -> incident -> recovery -> proof",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/ENGINEERING_PROOF.md",
    "bash scripts/check_public_pages_entrypoint.sh",
    "bash scripts/check_public_system_review_path.sh",
    "bash scripts/check_public_reviewer_quickstart.sh",
    "bash scripts/check_public_project_status.sh",
    "bash scripts/check_public_technical_capability_map.sh",
    "bash scripts/check_public_evidence_index.sh",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_demo_sdk.sh",
    "bash scripts/ci_smoke_public.sh",
    "docs/openapi.json",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "examples/python/demo_adapter_operation_plan.py",
    "examples/js/demo-adapter-operation-plan.mjs",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/BACKUP_RESTORE_EVIDENCE.md",
    "docs/public/RELEASE_ROLLBACK_EVIDENCE.md",
    "docs/public/SLO_CANARY_GATE_EVIDENCE.md",
    "docs/public/STAGED_PROMOTION_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/public/INFRA_STATE_DRIFT_EVIDENCE.md",
    "engineering reference -> demo -> API -> SDK -> workflow -> adapter -> observability -> incident -> release gate -> evidence",
    "docs/public/ENGINEERING_REVIEW_GUIDE.md",
    "docs/public/EVIDENCE_INDEX.md",
]:
    require(token in text, f"reviewer quickstart missing {token}")

for path in [
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/BACKUP_RESTORE_EVIDENCE.md",
    "docs/public/RELEASE_ROLLBACK_EVIDENCE.md",
    "docs/public/SLO_CANARY_GATE_EVIDENCE.md",
    "docs/public/STAGED_PROMOTION_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/public/INFRA_STATE_DRIFT_EVIDENCE.md",
    "docs/public/ENGINEERING_REVIEW_GUIDE.md",
    "docs/public/EVIDENCE_INDEX.md",
    "examples/python/demo_adapter_operation_plan.py",
    "examples/js/demo-adapter-operation-plan.mjs",
]:
    require((root / path).is_file(), f"reviewer quickstart target missing: {path}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (review_guide_path, "review guide"),
    (project_status_path, "project status"),
    (capability_map_path, "technical capability map"),
]:
    require("SYSTEM_REVIEW_PATH.md" in read(doc_path), f"{label} missing SYSTEM_REVIEW_PATH.md")
    require("REVIEWER_QUICKSTART.md" in read(doc_path), f"{label} missing reviewer quickstart")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for path in [
        "README.md",
        "index.html",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_reviewer_quickstart.sh",
    ]:
        require((root / path).is_file(), f"public export target missing: {path}")
    require("REVIEWER_QUICKSTART.md" in read(root_readme_path), "public README missing reviewer quickstart")
    require("SYSTEM_REVIEW_PATH.md" in read(root_readme_path), "public README missing system review path")
    require("REVIEWER_QUICKSTART.md" in read(index_path), "public Pages root missing reviewer quickstart")
    require("SYSTEM_REVIEW_PATH.md" in read(index_path), "public Pages root missing system review path")
    require(
        "check_public_system_review_path.sh" in read(public_smoke_path),
        "public smoke missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(public_smoke_path),
        "public smoke missing reviewer quickstart check",
    )
else:
    export_script = read(export_script_path)
    require("SYSTEM_REVIEW_PATH.md" in export_script, "export script missing system review path")
    require("REVIEWER_QUICKSTART.md" in export_script, "export script missing reviewer quickstart")
    require(
        'copy_path "scripts/check_public_system_review_path.sh"' in export_script,
        "export script missing system review path check copy",
    )
    require(
        'copy_path "scripts/check_public_reviewer_quickstart.sh"' in export_script,
        "export script missing reviewer quickstart check copy",
    )
    require(
        "check_public_system_review_path.sh" in read(private_smoke_path),
        "private smoke missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(private_smoke_path),
        "private smoke missing reviewer quickstart check",
    )
    require(
        "check_public_system_review_path.sh" in read(release_gate_path),
        "release gate missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(release_gate_path),
        "release gate missing reviewer quickstart check",
    )

blocked_runtime_patterns = [
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
for pattern in blocked_runtime_patterns:
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into reviewer quickstart: {pattern}")

if errors:
    for error in errors:
        print(f"reviewer_quickstart_error={error}", file=sys.stderr)
    raise SystemExit("public reviewer quickstart check failed")

print("public reviewer quickstart check ok: docs/public/REVIEWER_QUICKSTART.md")
PY
