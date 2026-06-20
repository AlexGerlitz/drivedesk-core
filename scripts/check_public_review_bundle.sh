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
doc_path = root / "docs/public/PUBLIC_REVIEW_BUNDLE.md"
evidence_path = root / "docs/public/evidence/public-review-bundle.sanitized.json"
runner_path = root / "scripts/run_public_review_bundle.sh"
checker_path = root / "scripts/check_public_review_bundle.sh"
docs_readme_path = root / "docs/public/README.md"
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
verification_matrix_path = root / "docs/public/PUBLIC_VERIFICATION_MATRIX.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


require(doc_path.is_file(), "missing docs/public/PUBLIC_REVIEW_BUNDLE.md")
require(evidence_path.is_file(), "missing public review bundle evidence JSON")
require(runner_path.is_file(), "missing scripts/run_public_review_bundle.sh")
require(checker_path.is_file(), "missing scripts/check_public_review_bundle.sh")

doc = read(doc_path)
for token in [
    "Public Review Bundle",
    "bash scripts/run_public_review_bundle.sh",
    "What This Proves",
    "docs/public/evidence/public-review-bundle.sanitized.json",
    "bash scripts/check_public_review_bundle.sh",
    "Boundary",
    "synthetic data and sanitized evidence only",
]:
    require(token in doc, f"review bundle doc missing {token}")

payload = json.loads(read(evidence_path))
require(payload.get("schema_version") == 1, "unexpected review bundle schema version")
require(payload.get("evidence_id") == "public_review_bundle", "unexpected review bundle evidence id")
require(payload.get("data_profile") == "synthetic_demo_data", "unexpected review bundle data profile")
require(payload.get("status") == "validated", "unexpected review bundle status")
require(payload.get("review_command") == "bash scripts/run_public_review_bundle.sh", "unexpected review command")
require(payload.get("contract_check") == "bash scripts/check_public_review_bundle.sh", "unexpected contract check")

redaction = payload.get("redaction", {})
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
]:
    require(redaction.get(key) is False, f"review bundle redaction flag must be false: {key}")

review_docs = payload.get("review_docs")
require(isinstance(review_docs, list) and len(review_docs) >= 6, "review_docs must list the review route")
for relative in review_docs or []:
    require(isinstance(relative, str), "review_doc must be a string")
    if isinstance(relative, str):
        require((root / relative).is_file(), f"review doc missing: {relative}")

included_checks = payload.get("included_checks")
require(isinstance(included_checks, list) and len(included_checks) >= 12, "included_checks must list the bundle checks")

runner = read(runner_path)
for command in included_checks or []:
    require(isinstance(command, str), "included check must be a string")
    if not isinstance(command, str):
        continue
    require(command.startswith("bash scripts/"), f"included check must be a bash script: {command}")
    script_path = command.removeprefix("bash ")
    require((root / script_path).is_file(), f"included check script missing: {script_path}")
    require(command in runner, f"runner missing included check: {command}")

require("public review bundle ok" in runner, "runner missing pass marker")

serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
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
    require(not pattern.search(serialized), f"review bundle evidence contains private marker: {pattern.pattern}")

docs_to_link = [
    docs_readme_path,
    quickstart_path,
    review_guide_path,
    verification_matrix_path,
    capability_map_path,
    evidence_index_path,
]
for path in docs_to_link:
    text = read(path)
    require("PUBLIC_REVIEW_BUNDLE.md" in text, f"{path.relative_to(root)} missing PUBLIC_REVIEW_BUNDLE.md")
    require("run_public_review_bundle.sh" in text, f"{path.relative_to(root)} missing run_public_review_bundle.sh")

index_payload = json.loads(read(evidence_index_json_path))
entries = index_payload.get("entries", [])
bundle_entries = [entry for entry in entries if entry.get("capability_id") == "public-review-bundle"]
require(len(bundle_entries) == 1, "evidence index must contain one public-review-bundle entry")
if bundle_entries:
    entry = bundle_entries[0]
    require(entry.get("public_doc") == "docs/public/PUBLIC_REVIEW_BUNDLE.md", "review bundle index public_doc mismatch")
    require(
        "docs/public/evidence/public-review-bundle.sanitized.json" in entry.get("evidence_files", []),
        "review bundle evidence JSON missing from evidence index entry",
    )
    require(
        "bash scripts/check_public_review_bundle.sh" in entry.get("verifiers", []),
        "review bundle verifier missing from evidence index entry",
    )

public_smoke = read(public_smoke_path)
if is_public_export or public_smoke_path.is_file():
    require("check_public_review_bundle.sh" in public_smoke, "public smoke missing review bundle check")

if is_public_export:
    root_readme = read(root_readme_path)
    index_html = read(index_html_path)
    require("PUBLIC_REVIEW_BUNDLE.md" in root_readme, "public README missing review bundle")
    require("run_public_review_bundle.sh" in root_readme, "public README missing review bundle command")
    require("docs/public/PUBLIC_REVIEW_BUNDLE.md" in index_html, "public Pages root missing review bundle link")
else:
    private_smoke = read(private_smoke_path)
    export_script = read(export_script_path)
    release_gate = read(release_gate_path)
    require("check_public_review_bundle.sh" in private_smoke, "private smoke missing review bundle check")
    require('copy_path "scripts/check_public_review_bundle.sh"' in export_script, "export script missing review bundle checker copy")
    require('copy_path "scripts/run_public_review_bundle.sh"' in export_script, "export script missing review bundle runner copy")
    require("PUBLIC_REVIEW_BUNDLE.md" in export_script, "export script missing review bundle doc reference")
    require("public-review-bundle.sanitized.json" in export_script, "export script missing review bundle evidence reference")
    require("check_public_review_bundle.sh" in export_script, "export script missing generated public smoke review bundle check")
    require("docs/public/PUBLIC_REVIEW_BUNDLE.md" in release_gate, "release gate missing review bundle doc required file")
    require(
        "docs/public/evidence/public-review-bundle.sanitized.json" in release_gate,
        "release gate missing review bundle evidence required file",
    )
    require("scripts/check_public_review_bundle.sh" in release_gate, "release gate missing review bundle checker required file")
    require("scripts/run_public_review_bundle.sh" in release_gate, "release gate missing review bundle runner required file")
    require("check_public_review_bundle.sh" in release_gate, "release gate missing review bundle check")

if errors:
    print("public review bundle check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"public review bundle check ok: included_checks={len(included_checks or [])}")
PY
