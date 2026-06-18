#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PORTFOLIO_DIR="${PORTFOLIO_DIR:-"$ROOT/infra/portfolio"}"
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

"$PYTHON_BIN" - <<'PY' "$PORTFOLIO_DIR" "$PUBLIC_DOCS" "$ROOT"
from __future__ import annotations

import json
import sys
from pathlib import Path

portfolio_dir = Path(sys.argv[1])
public_docs = Path(sys.argv[2])
root = Path(sys.argv[3])

contract_path = portfolio_dir / "portfolio-70-milestone.sanitized.json"
evidence_path = public_docs / "evidence/portfolio-70-milestone.sanitized.json"
doc_path = public_docs / "PORTFOLIO_70_MILESTONE.md"
adr_path = root / "docs/adr/0061-public-safe-portfolio-70-milestone.md"
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
    "core_platform_foundation",
    "public_reviewer_surface",
    "ci_release_safety",
    "iac_packaging_gitops",
    "observability_sre",
    "security_data_boundary",
    "recovery_drift_operations",
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

missing_references = sorted(
    relative
    for relative in referenced_paths
    if not (root / relative).exists()
    and relative
    not in {
        "scripts/ci_smoke.sh",
        "scripts/public_repo_release_gate.sh",
        "scripts/export_public_repo.sh",
    }
)

checks = {
    "milestone_files_present": not missing,
    "contract_and_evidence_match": contract == evidence,
    "milestone_shape_recorded": (
        contract.get("schema_version") == 1
        and contract.get("check") == "public_portfolio_70_milestone"
        and contract.get("milestone") == "devops_platform_portfolio_70"
        and contract.get("target", {}).get("current_milestone_percent") == 70
        and contract.get("target", {}).get("portfolio_scope") == "devops_platform_engineering"
    ),
    "completion_model_recorded": (
        contract.get("completion_model", {}).get("total_points_required") == 70
        and contract.get("completion_model", {}).get("points_recorded") == 70
        and contract.get("completion_model", {}).get("minimum_groups_required") == 7
        and contract.get("completion_model", {}).get("all_required_groups_complete") is True
        and points == 70
        and evidence_points == 70
    ),
    "all_required_groups_present": (
        group_ids == expected_groups
        and evidence_group_ids == expected_groups
        and all(group.get("status") == "complete" for group in groups)
        and all(group.get("human_value") for group in groups)
        and all(group.get("evidence") for group in groups)
        and all(group.get("checks") for group in groups)
    ),
    "referenced_artifacts_exist": not missing_references,
    "verification_chain_recorded": (
        contract.get("verification_chain", {}).get("private_smoke") == "bash scripts/ci_smoke.sh"
        and contract.get("verification_chain", {}).get("public_release_gate")
        == "bash scripts/public_repo_release_gate.sh"
        and contract.get("verification_chain", {}).get("milestone_check")
        == "bash scripts/check_public_portfolio_70_milestone.sh"
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
    ),
    "not_claiming_finished_saas": (
        contract.get("target", {}).get("commercial_saas_ready") is False
        and contract.get("decision", {}).get("production_commercial_saas_ready") is False
        and len(contract.get("remaining_to_100", [])) >= 5
        and "finished commercial SaaS" in doc_text
        and "mobile applications" in doc_text
    ),
    "docs_explain_technology_stack": (
        "Kubernetes" in doc_text
        and "Helm" in doc_text
        and "OpenTofu" in doc_text
        and "GitOps" in doc_text
        and "Prometheus" in doc_text
        and "Grafana" in doc_text
    ),
    "automation_wired": (
        (
            private_repo_mode
            and "check_public_portfolio_70_milestone.sh" in ci_smoke_text
            and "check_public_portfolio_70_milestone.sh" in public_gate_text
            and "check_public_portfolio_70_milestone.sh" in export_text
            and "PORTFOLIO_70_MILESTONE.md" in public_gate_text
            and "portfolio-70-milestone.sanitized.json" in public_gate_text
            and "0061-public-safe-portfolio-70-milestone.md" in public_gate_text
        )
        or (
            public_export_mode
            and "check_public_portfolio_70_milestone.sh" in public_smoke_text
            and doc_path.is_file()
            and evidence_path.is_file()
            and adr_path.is_file()
        )
    ),
    "decision_recorded": (
        contract.get("decision", {}).get("event_type") == "portfolio.milestone_70.reached"
        and contract.get("decision", {}).get("milestone_reached") is True
        and contract.get("decision", {}).get("claim")
        == "70 percent DevOps/platform portfolio milestone reached"
    ),
    "redaction_boundary_recorded": (
        contract.get("redaction", {}).get("hostnames_included") is False
        and contract.get("redaction", {}).get("addresses_included") is False
        and contract.get("redaction", {}).get("credentials_included") is False
        and contract.get("redaction", {}).get("raw_logs_included") is False
        and contract.get("redaction", {}).get("request_bodies_included") is False
        and contract.get("redaction", {}).get("production_data_included") is False
    ),
    "no_private_markers": not any(marker in text_to_scan for marker in private_markers),
}

failed = [name for name, ok in checks.items() if not ok]

if missing:
    print(f"missing milestone files: {', '.join(missing)}", file=sys.stderr)
if missing_references:
    print(f"missing referenced artifacts: {', '.join(missing_references)}", file=sys.stderr)
if failed:
    for name in failed:
        print(f"failed check: {name}", file=sys.stderr)
    raise SystemExit("public portfolio 70 milestone check failed")

print(
    "public portfolio 70 milestone check ok: "
    f"milestone={contract['milestone']} "
    f"points={points} "
    f"event={contract['decision']['event_type']}"
)
PY
