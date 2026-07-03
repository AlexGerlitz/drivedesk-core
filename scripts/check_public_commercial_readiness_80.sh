#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MATURITY_DIR="${MATURITY_DIR:-"$ROOT/infra/platform-maturity"}"
PUBLIC_DOCS="${PUBLIC_DOCS:-"$ROOT/docs/public"}"

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

"$PYTHON_BIN" - <<'PY' "$MATURITY_DIR" "$PUBLIC_DOCS" "$ROOT"
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

maturity_dir = Path(sys.argv[1])
public_docs = Path(sys.argv[2])
root = Path(sys.argv[3])

contract_path = maturity_dir / "commercial-readiness-80.sanitized.json"
evidence_path = public_docs / "evidence/commercial-readiness-80.sanitized.json"
doc_path = public_docs / "COMMERCIAL_READINESS_80.md"
adr_path = root / "docs/adr/0079-public-safe-commercial-readiness-80.md"
ci_smoke_path = root / "scripts/ci_smoke.sh"
public_gate_path = root / "scripts/public_repo_release_gate.sh"
export_path = root / "scripts/export_public_repo.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"

base_required_files = [
    contract_path,
    evidence_path,
    doc_path,
    adr_path,
]

private_repo_mode = ci_smoke_path.is_file() and public_gate_path.is_file() and export_path.is_file()
public_export_mode = public_smoke_path.is_file() and not public_gate_path.is_file()

required_files = list(base_required_files)
if private_repo_mode:
    required_files.extend([ci_smoke_path, public_gate_path, export_path])
elif public_export_mode:
    required_files.append(public_smoke_path)

missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]

contract = json.loads(contract_path.read_text(encoding="utf-8")) if contract_path.is_file() else {}
evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.is_file() else {}
doc_text = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
adr_text = adr_path.read_text(encoding="utf-8") if adr_path.is_file() else ""
ci_smoke_text = ci_smoke_path.read_text(encoding="utf-8") if ci_smoke_path.is_file() else ""
public_gate_text = public_gate_path.read_text(encoding="utf-8") if public_gate_path.is_file() else ""
export_text = export_path.read_text(encoding="utf-8") if export_path.is_file() else ""
public_smoke_text = public_smoke_path.read_text(encoding="utf-8") if public_smoke_path.is_file() else ""

groups = contract.get("evidence_groups", [])
evidence_groups = evidence.get("evidence_groups", [])
group_ids = {group.get("id") for group in groups}
evidence_group_ids = {group.get("id") for group in evidence_groups}
points = sum(group.get("points", 0) for group in groups)
evidence_points = sum(group.get("points", 0) for group in evidence_groups)

expected_groups = {
    "platform_maturity_foundation",
    "product_workbench_previews",
    "provider_sandbox_path",
    "action_approval_safety",
    "api_sdk_contract",
    "operations_release_evidence",
    "public_private_boundary",
    "commercial_gap_control",
}

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
    "185" + ".80",
    "152" + ".53",
    "/" + "opt/",
]

text_to_scan = "\n".join(
    path.read_text(encoding="utf-8").lower()
    for path in [contract_path, evidence_path, doc_path, adr_path]
    if path.is_file()
)

referenced_paths = set()
for payload in (contract, evidence):
    for group in payload.get("evidence_groups", []):
        referenced_paths.update(group.get("evidence", []))
        for check in group.get("checks", []):
            if check.startswith("bash "):
                referenced_paths.add(check.removeprefix("bash ").split()[0])
    chain = payload.get("verification_chain", {})
    for value in chain.values():
        if isinstance(value, str) and (
            value.startswith("scripts/")
            or value.startswith("bash scripts/")
            or value.startswith("docs/")
            or value.startswith("infra/")
        ):
            referenced_paths.add(value.removeprefix("bash ").split()[0])

generated_or_private_only = {
    "scripts/ci_smoke.sh",
    "scripts/ci_smoke_public.sh",
    "scripts/public_repo_release_gate.sh",
    "scripts/export_public_repo.sh",
}
missing_references = sorted(
    relative
    for relative in referenced_paths
    if not (root / relative).exists() and relative not in generated_or_private_only
)

checks = {
    "milestone_files_present": not missing,
    "contract_and_evidence_match": contract == evidence,
    "milestone_shape_recorded": (
        contract.get("schema_version") == 1
        and contract.get("check") == "public_commercial_readiness_80"
        and contract.get("milestone") == "commercial_readiness_80"
        and contract.get("target", {}).get("current_milestone_percent") == 80
        and contract.get("target", {}).get("engineering_scope") == "productized_business_os_foundation"
    ),
    "completion_model_recorded": (
        contract.get("completion_model", {}).get("total_points_required") == 80
        and contract.get("completion_model", {}).get("points_recorded") == 80
        and contract.get("completion_model", {}).get("minimum_groups_required") == 8
        and contract.get("completion_model", {}).get("all_required_groups_complete") is True
        and points == 80
        and evidence_points == 80
    ),
    "all_required_groups_present": (
        group_ids == expected_groups
        and evidence_group_ids == expected_groups
        and all(group.get("status") == "complete" for group in groups)
        and all(group.get("engineering_value") for group in groups)
        and all(group.get("evidence") for group in groups)
        and all(group.get("checks") for group in groups)
    ),
    "referenced_artifacts_exist": not missing_references,
    "verification_chain_recorded": (
        contract.get("verification_chain", {}).get("private_smoke") == "bash scripts/ci_smoke.sh"
        and contract.get("verification_chain", {}).get("public_release_gate")
        == "bash scripts/public_repo_release_gate.sh"
        and contract.get("verification_chain", {}).get("milestone_check")
        == "bash scripts/check_public_commercial_readiness_80.sh"
        and contract.get("verification_chain", {}).get("public_export_boundary")
        == "scripts/export_public_repo.sh"
    ),
    "public_boundary_recorded": (
        contract.get("public_boundary", {}).get("public_safe") is True
        and contract.get("public_boundary", {}).get("sanitized_evidence_only") is True
        and contract.get("public_boundary", {}).get("synthetic_demo_data_only") is True
        and contract.get("public_boundary", {}).get("no_customer_data") is True
        and contract.get("public_boundary", {}).get("no_private_hosts") is True
        and contract.get("public_boundary", {}).get("no_raw_logs") is True
        and contract.get("public_boundary", {}).get("no_runtime_secret_material") is True
        and contract.get("public_boundary", {}).get("no_provider_credentials") is True
        and contract.get("public_boundary", {}).get("no_external_mutation") is True
    ),
    "not_claiming_finished_saas": (
        contract.get("target", {}).get("commercial_saas_ready") is False
        and contract.get("decision", {}).get("production_commercial_saas_ready") is False
        and len(contract.get("remaining_to_100", [])) >= 8
        and "finished commercial SaaS product" in doc_text
        and "100 percent" in doc_text
    ),
    "docs_explain_commercial_path": (
        "Business Context Assistant" in doc_text
        and "approval gateway" in doc_text
        and "provider connector" in doc_text
        and "OpenAPI" in doc_text
        and "GitOps" in doc_text
        and "OpenTofu" in doc_text
    ),
    "automation_wired": (
        (
            private_repo_mode
            and "check_public_commercial_readiness_80.sh" in ci_smoke_text
            and "check_public_commercial_readiness_80.sh" in public_gate_text
            and "check_public_commercial_readiness_80.sh" in export_text
            and "COMMERCIAL_READINESS_80.md" in public_gate_text
            and "commercial-readiness-80.sanitized.json" in public_gate_text
            and "0079-public-safe-commercial-readiness-80.md" in public_gate_text
        )
        or (
            public_export_mode
            and "check_public_commercial_readiness_80.sh" in public_smoke_text
            and doc_path.is_file()
            and evidence_path.is_file()
            and adr_path.is_file()
        )
    ),
    "decision_recorded": (
        contract.get("decision", {}).get("event_type") == "commercial_readiness_80.reached"
        and contract.get("decision", {}).get("milestone_reached") is True
        and contract.get("decision", {}).get("claim")
        == "80 percent commercial readiness foundation reached"
    ),
    "redaction_recorded": (
        contract.get("redaction", {}).get("hostnames_included") is False
        and contract.get("redaction", {}).get("addresses_included") is False
        and contract.get("redaction", {}).get("credentials_included") is False
        and contract.get("redaction", {}).get("raw_logs_included") is False
        and contract.get("redaction", {}).get("request_bodies_included") is False
        and contract.get("redaction", {}).get("production_data_included") is False
    ),
    "adr_records_decision": (
        "Commercial Readiness 80 Percent Milestone" in adr_text
        and "public-safe" in adr_text
        and "does not claim finished" in adr_text
    ),
    "private_markers_absent": all(marker not in text_to_scan for marker in private_markers),
}

errors = [name for name, ok in checks.items() if not ok]
if missing:
    errors.append(f"missing required files: {missing}")
if missing_references:
    errors.append(f"missing referenced artifacts: {missing_references}")

ip_pattern = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
if ip_pattern.search(text_to_scan):
    errors.append("IP address found in commercial readiness milestone files")

if errors:
    print("public commercial readiness 80 milestone check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "public commercial readiness 80 milestone check ok: "
    f"milestone={contract.get('milestone')} points={points} "
    f"event={contract.get('decision', {}).get('event_type')}"
)
PY
