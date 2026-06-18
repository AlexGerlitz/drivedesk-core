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
guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
public_docs_readme_path = root / "docs/public/README.md"
root_readme_path = root / "README.md"
export_script_path = root / "scripts/export_public_repo.sh"
source_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
public_gate_path = root / "scripts/public_repo_release_gate.sh"

errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


require(guide_path.is_file(), "missing docs/public/ENGINEERING_REVIEW_GUIDE.md")
guide = read(guide_path)

for token in [
    "Engineering Review Guide",
    "docs/public/REVIEWER_QUICKSTART.md",
    "Live demo Operations, Incidents, and Proof tabs",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/check_public_reviewer_quickstart.sh",
    "bash scripts/check_public_review_guide.sh",
    "bash scripts/check_public_project_status.sh",
    "bash scripts/check_public_technical_capability_map.sh",
    "bash scripts/check_public_observability_proof.sh",
    "bash scripts/check_public_alert_routing.sh",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_demo_sdk.sh",
    "bash scripts/check_public_backup_restore.sh",
    "bash scripts/check_public_release_rollback.sh",
    "bash scripts/check_public_slo_canary_gate.sh",
    "bash scripts/check_public_staged_promotion.sh",
    "bash scripts/check_public_gitops_layout.sh",
    "bash scripts/check_public_opentofu_plan.sh",
    "docs/openapi.json",
    "GET /demo/public",
    "docs/public/SYSTEM_DESIGN.md",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/ENGINEERING_CASE_STUDY.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "sdk/generated/public-demo/",
]:
    require(token in guide, f"review guide missing {token}")

require(
    "REVIEWER_QUICKSTART.md" in read(public_docs_readme_path),
    "docs/public README missing REVIEWER_QUICKSTART.md",
)
require(
    "ENGINEERING_REVIEW_GUIDE.md" in read(public_docs_readme_path),
    "docs/public README missing ENGINEERING_REVIEW_GUIDE.md",
)
require(
    "PROJECT_STATUS.md" in read(public_docs_readme_path),
    "docs/public README missing PROJECT_STATUS.md",
)
require(
    "TECHNICAL_CAPABILITY_MAP.md" in read(public_docs_readme_path),
    "docs/public README missing TECHNICAL_CAPABILITY_MAP.md",
)
require(
    "OBSERVABILITY_PROOF.md" in read(public_docs_readme_path),
    "docs/public README missing OBSERVABILITY_PROOF.md",
)
require(
    "ALERT_ROUTING_EVIDENCE.md" in read(public_docs_readme_path),
    "docs/public README missing ALERT_ROUTING_EVIDENCE.md",
)
require(
    "INCIDENT_RESPONSE_DEMO.md" in read(public_docs_readme_path),
    "docs/public README missing INCIDENT_RESPONSE_DEMO.md",
)

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export and root_readme_path.is_file():
    root_readme = read(root_readme_path)
    require("REVIEWER_QUICKSTART.md" in root_readme, "root README missing reviewer quickstart link")
    require("ENGINEERING_REVIEW_GUIDE.md" in root_readme, "root README missing review guide link")
    require("Fast Review" in root_readme, "root README missing Fast Review section")

if export_script_path.is_file():
    export_script = read(export_script_path)
    require("REVIEWER_QUICKSTART.md" in export_script, "export script missing reviewer quickstart")
    require("ENGINEERING_REVIEW_GUIDE.md" in export_script, "export script missing review guide")
    require("check_public_review_guide.sh" in export_script, "export script missing review guide check")

if source_smoke_path.is_file():
    require("check_public_reviewer_quickstart.sh" in read(source_smoke_path), "source smoke missing reviewer quickstart check")
    require("check_public_review_guide.sh" in read(source_smoke_path), "source smoke missing review guide check")

if public_smoke_path.is_file():
    require("check_public_reviewer_quickstart.sh" in read(public_smoke_path), "public smoke missing reviewer quickstart check")
    require("check_public_review_guide.sh" in read(public_smoke_path), "public smoke missing review guide check")

if public_gate_path.is_file():
    gate_text = read(public_gate_path)
    require("REVIEWER_QUICKSTART.md" in gate_text, "release gate missing reviewer quickstart doc")
    require("check_public_reviewer_quickstart.sh" in gate_text, "release gate missing reviewer quickstart check")
    require("ENGINEERING_REVIEW_GUIDE.md" in gate_text, "release gate missing review guide doc")
    require("check_public_review_guide.sh" in gate_text, "release gate missing review guide check")

for path in [
    "docs/public/SYSTEM_DESIGN.md",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/ENGINEERING_CASE_STUDY.md",
    "docs/public/SANITIZED_EVIDENCE.md",
]:
    require((root / path).is_file(), f"review guide evidence target missing: {path}")

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
lowered = guide.lower()
for pattern in blocked_runtime_patterns:
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into review guide: {pattern}")

if errors:
    for error in errors:
        print(f"review_guide_error={error}", file=sys.stderr)
    raise SystemExit("public review guide check failed")

print("public review guide check ok: docs/public/ENGINEERING_REVIEW_GUIDE.md")
PY
