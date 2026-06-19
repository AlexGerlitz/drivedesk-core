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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
proof_doc_path = root / "docs/public/ENGINEERING_PROOF.md"
public_readme_path = root / "docs/public/README.md"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
public_gate_path = root / "scripts/public_repo_release_gate.sh"

for path in [demo_data_path, demo_app_path, demo_html_path, proof_doc_path, public_readme_path]:
    require(path.is_file(), f"missing required proof file: {relative(path)}")

source = read_text(demo_data_path)
match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", source, flags=re.DOTALL)
require(match is not None, "demo-data.js payload assignment missing")
static_payload = json.loads(match.group(1)) if match else {}
api_payload = build_public_demo_payload()

static_proof = static_payload.get("engineeringProof", {})
api_proof = api_payload.get("engineeringProof", {})

require(static_proof == api_proof, "static and API engineeringProof payloads differ")
require(
    static_payload.get("incidentResponse") == api_payload.get("incidentResponse"),
    "static and API incidentResponse payloads differ",
)
require(
    static_payload.get("endToEndScenario") == api_payload.get("endToEndScenario"),
    "static and API endToEndScenario payloads differ",
)
require(
    static_payload.get("businessControlTower") == api_payload.get("businessControlTower"),
    "static and API businessControlTower payloads differ",
)
require(static_proof.get("milestone") == "engineering_70", "engineeringProof milestone mismatch")
require(static_proof.get("status") == "validated", "engineeringProof status mismatch")
require(len(static_proof.get("summary", [])) >= 4, "engineeringProof summary too short")

expected_gates = {
    "Core smoke": "bash scripts/ci_smoke_public.sh",
    "Public demo API": "bash scripts/check_public_demo_api.sh",
    "Backup and restore": "bash scripts/check_public_backup_restore.sh",
    "Release safety": "bash scripts/check_public_release_rollback.sh && bash scripts/check_public_staged_promotion.sh",
    "GitOps and IaC": "bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh",
}
gate_by_name = {gate.get("name"): gate for gate in static_proof.get("gates", []) if isinstance(gate, dict)}
require(set(expected_gates).issubset(gate_by_name), "engineeringProof required gates missing")
for name, command in expected_gates.items():
    gate = gate_by_name.get(name, {})
    require(gate.get("status") == "passed", f"{name} gate is not passed")
    require(gate.get("command") == command, f"{name} command mismatch")
    require(bool(gate.get("evidence")), f"{name} evidence missing")

expected_evidence_paths = {
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "docs/public/REVIEWER_QUICKSTART.md",
    "docs/public/PLATFORM_MATURITY_70.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/SYSTEM_DESIGN.md",
    "sdk/generated/public-demo/",
}
evidence_paths = {
    item.get("path")
    for item in static_proof.get("evidence", [])
    if isinstance(item, dict)
}
require(expected_evidence_paths.issubset(evidence_paths), "engineeringProof evidence paths missing")
for item in static_proof.get("evidence", []):
    if not isinstance(item, dict):
        continue
    item_path = item.get("path", "")
    require(bool(item.get("title")), f"evidence title missing for {item_path}")
    require(bool(item.get("summary")), f"evidence summary missing for {item_path}")
    require((root / item_path).exists(), f"evidence target missing: {item_path}")

end_to_end = static_payload.get("endToEndScenario", {})
require(
    end_to_end.get("id") == "scenario-approval-notification-adapter-incident",
    "endToEndScenario id mismatch",
)
require(end_to_end.get("status") == "reviewable", "endToEndScenario status mismatch")
require(end_to_end.get("currentStep") == "incident_resolved", "endToEndScenario current step mismatch")
chain = end_to_end.get("chain", [])
require(isinstance(chain, list) and len(chain) >= 6, "endToEndScenario chain too short")
chain_steps = {step.get("step") for step in chain if isinstance(step, dict)}
require(
    {"approval", "notification", "adapter", "incident", "recovery", "proof"}.issubset(chain_steps),
    "endToEndScenario required steps missing",
)
chain_evidence = {step.get("evidence") for step in chain if isinstance(step, dict)}
require(
    {
        "workflow.contract_approved",
        "notification.manager_signature_task.created",
        "integration.accounting_export.requested",
        "integration.incident.status_changed",
        "postcheck.gates.passed",
        "docs/public/ENGINEERING_PROOF.md",
    }.issubset(chain_evidence),
    "endToEndScenario evidence chain missing",
)
require(
    "docs/public/ENGINEERING_PROOF.md" in set(end_to_end.get("proof", [])),
    "endToEndScenario proof list missing engineering proof doc",
)

available_or_generated_public_scripts = {
    "scripts/ci_smoke_public.sh",
}
export_script_text = read_text(export_script_path)
for command in expected_gates.values():
    for part in command.split("&&"):
        tokens = part.strip().split()
        if len(tokens) < 2 or tokens[0] != "bash":
            errors.append(f"unsupported proof command shape: {part.strip()}")
            continue
        script_path = tokens[1]
        exists_now = (root / script_path).is_file()
        generated_by_export = script_path in available_or_generated_public_scripts and script_path in export_script_text
        require(exists_now or generated_by_export, f"proof command script missing: {script_path}")

html = read_text(demo_html_path)
for token in [
    'data-view="proof"',
    'data-view="incidents"',
    'id="view-proof"',
    'id="view-incidents"',
    'id="incidentSummaryRows"',
    'id="incidentRows"',
    'id="incidentTimelineRows"',
    'id="endToEndScenarioRows"',
    'id="endToEndScenarioMeta"',
    'id="proofSummaryRows"',
    'id="proofGateRows"',
    'id="proofEvidenceRows"',
]:
    require(token in html, f"public demo HTML missing {token}")

app = read_text(demo_app_path)
for token in [
    "fillIncidentResponse",
    "payload.incidentResponse",
    "fillEndToEndScenario",
    "payload.endToEndScenario",
    "fillEngineeringProof",
    "payload.engineeringProof",
    "engineeringProof.summary",
    "engineeringProof.gates",
    "engineeringProof.evidence",
]:
    require(token in app, f"public demo app missing {token}")

openapi = build_app().openapi()
public_demo_schema = openapi.get("components", {}).get("schemas", {}).get("PublicDemoRead", {})
required_fields = set(public_demo_schema.get("required", []))
require("engineeringProof" in required_fields, "OpenAPI PublicDemoRead does not require engineeringProof")
require("recoveryEvidence" in required_fields, "OpenAPI PublicDemoRead does not require recoveryEvidence")
require("alertRouting" in required_fields, "OpenAPI PublicDemoRead does not require alertRouting")
require("incidentResponse" in required_fields, "OpenAPI PublicDemoRead does not require incidentResponse")
require("endToEndScenario" in required_fields, "OpenAPI PublicDemoRead does not require endToEndScenario")

sdk_files = [
    root / "sdk/generated/public-demo/openapi-client-manifest.json",
    root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py",
    root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs",
    root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts",
]
for path in sdk_files:
    require(path.is_file(), f"generated SDK file missing: {relative(path)}")
    require("engineeringProof" in read_text(path), f"generated SDK file missing engineeringProof: {relative(path)}")
    require("alertRouting" in read_text(path), f"generated SDK file missing alertRouting: {relative(path)}")
    require("incidentResponse" in read_text(path), f"generated SDK file missing incidentResponse: {relative(path)}")
    require("endToEndScenario" in read_text(path), f"generated SDK file missing endToEndScenario: {relative(path)}")

require(
    "build_adapter_operation_plan" in read_text(root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py"),
    "generated Python SDK missing adapter operation helper",
)
require(
    "buildAdapterOperationPlan" in read_text(root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs"),
    "generated JavaScript SDK missing adapter operation helper",
)
require(
    "AdapterOperationPlan" in read_text(root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts"),
    "generated TypeScript SDK missing adapter operation type",
)

proof_doc = read_text(proof_doc_path)
for token in [
    "engineeringProof",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/ci_smoke_public.sh",
    "Core smoke",
    "Public demo API",
    "Backup and restore",
    "Release safety",
    "GitOps and IaC",
    "approval -> notification -> adapter -> incident -> recovery -> proof",
    "endToEndScenario",
    "adapter operation plan helpers",
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "docs/public/REVIEWER_QUICKSTART.md",
]:
    require(token in proof_doc, f"ENGINEERING_PROOF.md missing {token}")

public_readme = read_text(public_readme_path)
require("ENGINEERING_PROOF.md" in public_readme, "public docs README missing ENGINEERING_PROOF.md")

if export_script_path.is_file():
    for token in [
        'copy_path "scripts/check_public_engineering_proof.sh"',
        "bash scripts/check_public_engineering_proof.sh",
        "ENGINEERING_PROOF.md",
    ]:
        require(token in export_script_text, f"export script missing {token}")

if private_smoke_path.is_file():
    require(
        "check_public_engineering_proof.sh" in read_text(private_smoke_path),
        "private ci_smoke.sh missing engineering proof check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_engineering_proof.sh" in read_text(public_smoke_path),
        "public ci_smoke_public.sh missing engineering proof check",
    )

if public_gate_path.is_file():
    require(
        "check_public_engineering_proof.sh" in read_text(public_gate_path),
        "public repo release gate missing engineering proof check",
    )

private_markers = [
    "auto" + "school54",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "215" + "689",
    "185" + ".80",
    "152" + ".53",
    "/" + "opt/",
]
scan_text = json.dumps(static_proof, sort_keys=True).lower()
for marker in private_markers:
    require(marker not in scan_text, f"private marker leaked into engineeringProof: {marker}")

if errors:
    for error in errors:
        print(f"proof_error={error}", file=sys.stderr)
    raise SystemExit("public engineering proof check failed")

print(
    "public engineering proof check ok: "
    f"milestone={static_proof['milestone']} "
    f"gates={len(static_proof['gates'])} "
    f"evidence={len(static_proof['evidence'])}"
)
PY
