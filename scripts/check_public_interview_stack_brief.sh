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
doc_path = root / "docs/public/INTERVIEW_STACK_BRIEF.md"
evidence_path = root / "docs/public/evidence/interview-stack-brief.sanitized.json"
docs_readme_path = root / "docs/public/README.md"
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
verification_matrix_path = root / "docs/public/PUBLIC_VERIFICATION_MATRIX.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
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


require(doc_path.is_file(), "missing docs/public/INTERVIEW_STACK_BRIEF.md")
require(evidence_path.is_file(), "missing interview stack brief evidence JSON")

doc = read(doc_path)
required_doc_tokens = [
    "Interview Stack Brief",
    "How To Describe The Project",
    "Stack Map",
    "Interview Talking Points",
    "What Is Ready Versus Not Ready",
    "Fast Proof Path",
    "bash scripts/check_public_interview_stack_brief.sh",
    "bash scripts/run_public_review_bundle.sh",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/PUBLIC_VERIFICATION_MATRIX.md",
    "docs/public/EVIDENCE_INDEX.md",
    "docs/public/evidence/interview-stack-brief.sanitized.json",
    "Boundary",
]
for token in required_doc_tokens:
    require(token in doc, f"interview stack brief missing {token}")

stack_rows = [
    "Python / FastAPI",
    "PostgreSQL / Alembic",
    "Redis / Workers / Outbox",
    "OpenAPI / SDK",
    "Integration Hub / Adapters",
    "Business Control Tower",
    "Docker / Compose",
    "Kubernetes / Helm",
    "GitOps / Argo CD",
    "OpenTofu / Terraform",
    "CI/CD / GitHub Actions",
    "Observability / Prometheus / Grafana / Loki",
    "Reliability / Recovery",
    "Security / Public-Private Boundary",
    "Public Demo / Pages",
]
for stack in stack_rows:
    require(stack in doc, f"interview stack brief missing stack row: {stack}")

for phrase in [
    "What It Does",
    "Current State",
    "What Remains",
    "Modular monolith first",
    "Outbox and workers",
    "Integration Hub",
    "GitOps/IaC",
    "Observability",
    "Public/private split",
]:
    require(phrase in doc, f"interview stack brief missing phrase: {phrase}")

payload = json.loads(read(evidence_path))
require(payload.get("schema_version") == 1, "unexpected interview stack brief schema version")
require(payload.get("evidence_id") == "interview_stack_brief", "unexpected interview stack brief evidence id")
require(payload.get("data_profile") == "synthetic_demo_data", "unexpected interview stack brief data profile")
require(payload.get("status") == "validated", "unexpected interview stack brief status")
require(payload.get("public_doc") == "docs/public/INTERVIEW_STACK_BRIEF.md", "unexpected interview stack brief public_doc")
require(
    payload.get("contract_check") == "bash scripts/check_public_interview_stack_brief.sh",
    "unexpected interview stack brief contract check",
)
require(payload.get("proof_command") == "bash scripts/run_public_review_bundle.sh", "unexpected interview stack proof command")
require(payload.get("boundary"), "interview stack brief missing boundary")

payload_stacks = payload.get("stack_groups")
require(isinstance(payload_stacks, list), "stack_groups must be a list")
for stack in stack_rows:
    require(stack in (payload_stacks or []), f"evidence missing stack group: {stack}")

related_docs = payload.get("related_docs")
require(isinstance(related_docs, list) and len(related_docs or []) >= 5, "related_docs must list related public docs")
for relative in related_docs or []:
    require(isinstance(relative, str), "related doc must be a string")
    if isinstance(relative, str):
        require((root / relative).is_file(), f"related doc missing: {relative}")

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
    require(redaction.get(key) is False, f"interview stack redaction flag must be false: {key}")

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
    require(not pattern.search(serialized), f"interview stack evidence contains private marker: {pattern.pattern}")

index_payload = json.loads(read(evidence_index_json_path))
entries = index_payload.get("entries", [])
brief_entries = [entry for entry in entries if entry.get("capability_id") == "interview-stack-brief"]
require(len(brief_entries) == 1, "evidence index must contain one interview-stack-brief entry")
if brief_entries:
    entry = brief_entries[0]
    require(entry.get("public_doc") == "docs/public/INTERVIEW_STACK_BRIEF.md", "interview stack index public_doc mismatch")
    require(
        "docs/public/evidence/interview-stack-brief.sanitized.json" in entry.get("evidence_files", []),
        "interview stack evidence JSON missing from evidence index entry",
    )
    require(
        "bash scripts/check_public_interview_stack_brief.sh" in entry.get("verifiers", []),
        "interview stack verifier missing from evidence index entry",
    )

for path in [
    docs_readme_path,
    quickstart_path,
    review_guide_path,
    verification_matrix_path,
    project_status_path,
    capability_map_path,
    evidence_index_path,
]:
    text = read(path)
    require("INTERVIEW_STACK_BRIEF.md" in text, f"{path.relative_to(root)} missing INTERVIEW_STACK_BRIEF.md")
    require("check_public_interview_stack_brief.sh" in text, f"{path.relative_to(root)} missing interview stack checker")

public_smoke = read(public_smoke_path)
if is_public_export or public_smoke_path.is_file():
    require("check_public_interview_stack_brief.sh" in public_smoke, "public smoke missing interview stack check")

if is_public_export:
    root_readme = read(root_readme_path)
    index_html = read(index_html_path)
    require("INTERVIEW_STACK_BRIEF.md" in root_readme, "public README missing interview stack brief")
    require("docs/public/INTERVIEW_STACK_BRIEF.md" in index_html, "public Pages root missing interview stack brief link")
else:
    private_smoke = read(private_smoke_path)
    export_script = read(export_script_path)
    release_gate = read(release_gate_path)
    require("check_public_interview_stack_brief.sh" in private_smoke, "private smoke missing interview stack check")
    require('copy_path "scripts/check_public_interview_stack_brief.sh"' in export_script, "export script missing interview stack checker copy")
    require("INTERVIEW_STACK_BRIEF.md" in export_script, "export script missing interview stack brief doc reference")
    require("interview-stack-brief.sanitized.json" in export_script, "export script missing interview stack evidence reference")
    require("check_public_interview_stack_brief.sh" in export_script, "export script missing generated public smoke interview stack check")
    require("docs/public/INTERVIEW_STACK_BRIEF.md" in release_gate, "release gate missing interview stack brief required file")
    require(
        "docs/public/evidence/interview-stack-brief.sanitized.json" in release_gate,
        "release gate missing interview stack evidence required file",
    )
    require("scripts/check_public_interview_stack_brief.sh" in release_gate, "release gate missing interview stack checker required file")
    require("check_public_interview_stack_brief.sh" in release_gate, "release gate missing interview stack check")

if errors:
    print("public interview stack brief check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"public interview stack brief check ok: stack_groups={len(stack_rows)}")
PY
