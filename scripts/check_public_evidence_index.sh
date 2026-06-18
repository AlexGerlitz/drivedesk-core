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
index_doc_path = root / "docs/public/EVIDENCE_INDEX.md"
index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
engineering_proof_path = root / "docs/public/ENGINEERING_PROOF.md"
sanitized_evidence_path = root / "docs/public/SANITIZED_EVIDENCE.md"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
generated_export_only_files = {
    "docs/openapi.json",
    "index.html",
    "scripts/ci_smoke_public.sh",
}

errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


require(index_doc_path.is_file(), "missing docs/public/EVIDENCE_INDEX.md")
require(index_json_path.is_file(), "missing public evidence index JSON")

payload = json.loads(read(index_json_path))
require(payload.get("schema_version") == 1, "unexpected evidence index schema version")
require(payload.get("index_id") == "drivedesk-core-public-evidence-index", "unexpected evidence index id")
require(payload.get("data_profile") == "synthetic_fake_data", "unexpected evidence index data profile")
require(payload.get("status") == "validated", "unexpected evidence index status")
require(payload.get("public_root_url") == "https://alexgerlitz.github.io/drivedesk-core/", "unexpected public root URL")

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
    require(redaction.get(key) is False, f"redaction flag must be false: {key}")

entries = payload.get("entries")
require(isinstance(entries, list), "entries must be a list")
require(len(entries or []) >= 12, "expected at least twelve evidence index entries")

seen_ids: set[str] = set()
allowed_absolute_url = "https://alexgerlitz.github.io/drivedesk-core/"
private_patterns = [
    re.compile(r"auto\s*school\s*54", re.IGNORECASE),
    re.compile("auto" + "school54", re.IGNORECASE),
    re.compile("land" + "vps", re.IGNORECASE),
    re.compile("duck" + "dns", re.IGNORECASE),
    re.compile("xr" + "ay", re.IGNORECASE),
    re.compile("vl" + "ess", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
]

public_smoke = read(public_smoke_path)
private_smoke = read(private_smoke_path)
export_script = read(export_script_path)
release_gate = read(release_gate_path)

for entry in entries or []:
    capability_id = entry.get("capability_id")
    require(isinstance(capability_id, str) and capability_id, "entry missing capability_id")
    if isinstance(capability_id, str):
        require(capability_id not in seen_ids, f"duplicate capability_id: {capability_id}")
        seen_ids.add(capability_id)

    require(entry.get("status") == "validated", f"{capability_id} status is not validated")
    require(isinstance(entry.get("title"), str) and entry["title"], f"{capability_id} missing title")
    require(isinstance(entry.get("boundary"), str) and entry["boundary"], f"{capability_id} missing boundary")

    public_doc = entry.get("public_doc")
    require(isinstance(public_doc, str) and public_doc.endswith(".md"), f"{capability_id} invalid public_doc")
    if isinstance(public_doc, str):
        require((root / public_doc).is_file(), f"{capability_id} public_doc missing: {public_doc}")

    evidence_files = entry.get("evidence_files")
    require(isinstance(evidence_files, list) and evidence_files, f"{capability_id} missing evidence_files")
    for evidence_file in evidence_files or []:
        require(isinstance(evidence_file, str), f"{capability_id} evidence file must be a string")
        if isinstance(evidence_file, str):
            if is_public_export or evidence_file not in generated_export_only_files:
                require((root / evidence_file).is_file(), f"{capability_id} evidence file missing: {evidence_file}")

    verifiers = entry.get("verifiers")
    require(isinstance(verifiers, list) and verifiers, f"{capability_id} missing verifiers")
    for verifier in verifiers or []:
        require(isinstance(verifier, str), f"{capability_id} verifier must be a string")
        if not isinstance(verifier, str):
            continue
        require(verifier.startswith("bash scripts/"), f"{capability_id} verifier must use bash scripts/: {verifier}")
        script_path = verifier.removeprefix("bash ")
        if is_public_export or script_path not in generated_export_only_files:
            require((root / script_path).is_file(), f"{capability_id} verifier script missing: {script_path}")
        if script_path != "scripts/ci_smoke_public.sh" and (is_public_export or public_smoke_path.is_file()):
            require(script_path in public_smoke, f"{capability_id} verifier missing from public smoke: {script_path}")

    public_urls = entry.get("public_urls")
    require(isinstance(public_urls, list) and public_urls, f"{capability_id} missing public_urls")
    for url in public_urls or []:
        require(isinstance(url, str), f"{capability_id} public URL must be a string")
        if not isinstance(url, str):
            continue
        is_allowed_absolute = url.startswith(allowed_absolute_url)
        is_allowed_relative = not re.match(r"^[a-z]+://", url)
        require(is_allowed_absolute or is_allowed_relative, f"{capability_id} unexpected public URL: {url}")
        if is_allowed_relative:
            target = root / url
            if url.endswith("/"):
                target = target / "index.html"
            if is_public_export:
                require(target.exists(), f"{capability_id} public URL target missing: {url}")

serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
for pattern in private_patterns:
    require(not pattern.search(serialized), f"evidence index contains private marker: {pattern.pattern}")

doc = read(index_doc_path)
for token in [
    "Public Evidence Index",
    "docs/public/evidence/public-evidence-index.sanitized.json",
    "bash scripts/check_public_evidence_index.sh",
    "Indexed Capability Groups",
    "Boundary",
    "Verification",
]:
    require(token in doc, f"evidence index doc missing {token}")

for path in [
    docs_readme_path,
    review_guide_path,
    project_status_path,
    capability_map_path,
    engineering_proof_path,
    sanitized_evidence_path,
]:
    text = read(path)
    require("EVIDENCE_INDEX.md" in text, f"{path.relative_to(root)} missing EVIDENCE_INDEX.md")
    require(
        "public-evidence-index.sanitized.json" in text,
        f"{path.relative_to(root)} missing public evidence JSON reference",
    )

if is_public_export:
    require("EVIDENCE_INDEX.md" in read(root_readme_path), "public README missing evidence index")
    require("EVIDENCE_INDEX.md" in read(index_html_path), "public Pages root missing evidence index")
    require("check_public_evidence_index.sh" in public_smoke, "public smoke missing evidence index check")
else:
    require("EVIDENCE_INDEX.md" in export_script, "export script missing evidence index doc")
    require(
        'copy_path "scripts/check_public_evidence_index.sh"' in export_script,
        "export script missing evidence index checker copy",
    )
    require("check_public_evidence_index.sh" in private_smoke, "private smoke missing evidence index check")
    require("check_public_evidence_index.sh" in release_gate, "release gate missing evidence index check")

if release_gate_path.is_file():
    require("docs/public/EVIDENCE_INDEX.md" in release_gate, "release gate missing evidence index required file")
    require(
        "docs/public/evidence/public-evidence-index.sanitized.json" in release_gate,
        "release gate missing evidence index JSON required file",
    )

if errors:
    print("public evidence index check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"public evidence index check ok: entries={len(entries or [])}")
PY
