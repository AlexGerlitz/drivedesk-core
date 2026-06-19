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
matrix_path = root / "docs/public/PUBLIC_VERIFICATION_MATRIX.md"
docs_readme_path = root / "docs/public/README.md"
quickstart_path = root / "docs/public/REVIEWER_QUICKSTART.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
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


require(matrix_path.is_file(), "missing docs/public/PUBLIC_VERIFICATION_MATRIX.md")
text = read(matrix_path)

required_tokens = [
    "Public Verification Matrix",
    "claim to the artifact, verifier command, and pass signal",
    "Claim | Evidence | Verifier | Pass signal",
    "Public entrypoint is navigable",
    "Demo health is live-verifiable",
    "OpenAPI contract is not stale",
    "Generated SDK matches the API",
    "Business OS route is connected",
    "Control Tower workflow is executable as a safe preview",
    "Action execution is gated and auditable",
    "Integration runtime and repair paths are connected",
    "Notification delivery has retry and review evidence",
    "Observability and alert routing are reviewable",
    "Incident and repair surfaces close the loop",
    "Release safety is covered by drills",
    "GitOps and infrastructure contracts are reviewable",
    "Private runtime evidence stays sanitized",
    "Evidence index and export boundary stay consistent",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/check_public_verification_matrix.sh",
    "Boundary",
]
for token in required_tokens:
    require(token in text, f"verification matrix missing {token}")

expected_paths = [
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "docs/public/REVIEWER_QUICKSTART.md",
    "docs/public/PUBLIC_DEMO_HEALTH.md",
    "docs/public/OPENAPI_DRIFT.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/PLATFORM_TOUR.md",
    "docs/public/BUSINESS_CONTROL_TOWER.md",
    "docs/public/BUSINESS_ACTION_EXECUTION.md",
    "docs/public/BUSINESS_APPROVAL_GATEWAY.md",
    "docs/public/INTEGRATION_RUNTIME.md",
    "docs/public/INTEGRATION_EXECUTION.md",
    "docs/public/INTEGRATION_REPAIR.md",
    "docs/public/NOTIFICATION_DELIVERY.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/OBSERVABILITY_DASHBOARD.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/BACKUP_RESTORE_EVIDENCE.md",
    "docs/public/RELEASE_ROLLBACK_EVIDENCE.md",
    "docs/public/SLO_CANARY_GATE_EVIDENCE.md",
    "docs/public/STAGED_PROMOTION_EVIDENCE.md",
    "docs/public/HELM_CHART.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/public/INFRA_STATE_DRIFT_EVIDENCE.md",
    "docs/public/RUNTIME_ROLLOUT_EVIDENCE.md",
    "docs/public/PRIVATE_INFRA_VALIDATION.md",
    "docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md",
    "docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md",
    "docs/public/EVIDENCE_INDEX.md",
    "docs/public/SANITIZED_EVIDENCE.md",
]
for path in expected_paths:
    require(path in text, f"verification matrix missing path {path}")
    require((root / path).is_file(), f"verification matrix target missing: {path}")

expected_scripts = [
    "scripts/check_public_pages_entrypoint.sh",
    "scripts/check_public_system_review_path.sh",
    "scripts/check_public_reviewer_quickstart.sh",
    "scripts/check_public_demo_health.sh",
    "scripts/check_public_openapi_drift.sh",
    "scripts/check_public_demo_sdk.sh",
    "scripts/check_public_platform_tour.sh",
    "scripts/check_public_demo_api.sh",
    "scripts/check_public_business_control_tower.sh",
    "scripts/check_public_business_intake_pipeline.sh",
    "scripts/check_public_business_task_handoff.sh",
    "scripts/check_public_business_notification_channels.sh",
    "scripts/check_public_business_action_execution.sh",
    "scripts/check_public_business_approval_gateway.sh",
    "scripts/check_public_integration_runtime.sh",
    "scripts/check_public_integration_execution.sh",
    "scripts/check_public_integration_repair.sh",
    "scripts/check_public_notification_delivery.sh",
    "scripts/check_public_observability_proof.sh",
    "scripts/check_public_observability_dashboard.sh",
    "scripts/check_public_alert_routing.sh",
    "scripts/check_public_engineering_proof.sh",
    "scripts/check_public_backup_restore.sh",
    "scripts/check_public_release_rollback.sh",
    "scripts/check_public_slo_canary_gate.sh",
    "scripts/check_public_staged_promotion.sh",
    "scripts/check_public_helm_render.sh",
    "scripts/check_public_gitops_layout.sh",
    "scripts/check_public_opentofu_plan.sh",
    "scripts/check_public_infra_state_drift.sh",
    "scripts/check_public_runtime_rollout.sh",
    "scripts/check_public_private_infra_validation.sh",
    "scripts/check_public_private_infra_scheduled_validation.sh",
    "scripts/check_public_private_infra_scheduled_alerting.sh",
    "scripts/check_public_evidence_index.sh",
    "scripts/check_public_export_secrets.sh",
    "scripts/check_public_verification_matrix.sh",
]
generated_export_only_scripts = {
    "scripts/check_public_export_secrets.sh",
}
for script in expected_scripts:
    require(f"bash {script}" in text or script == "scripts/check_public_verification_matrix.sh", f"verification matrix missing command {script}")
    if is_public_export or script not in generated_export_only_scripts:
        require((root / script).is_file(), f"verification matrix script missing: {script}")

row_count = sum(
    1
    for line in text.splitlines()
    if line.startswith("| ")
    and not line.startswith("| ---")
    and not line.startswith("| Claim")
)
require(row_count >= 15, f"expected at least 15 verification matrix rows, got {row_count}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (quickstart_path, "reviewer quickstart"),
    (review_guide_path, "review guide"),
    (capability_map_path, "technical capability map"),
    (evidence_index_path, "evidence index"),
]:
    doc_text = read(doc_path)
    require("PUBLIC_VERIFICATION_MATRIX.md" in doc_text, f"{label} missing verification matrix reference")
    require("check_public_verification_matrix.sh" in doc_text, f"{label} missing verification matrix checker reference")

require("public-verification-matrix" in read(evidence_index_json_path), "evidence index JSON missing verification matrix entry")

if is_public_export:
    require("PUBLIC_VERIFICATION_MATRIX.md" in read(root_readme_path), "public README missing verification matrix")
    require("PUBLIC_VERIFICATION_MATRIX.md" in read(index_html_path), "public Pages root missing verification matrix")
    require("check_public_verification_matrix.sh" in read(public_smoke_path), "public smoke missing verification matrix check")
else:
    export_script = read(export_script_path)
    require("PUBLIC_VERIFICATION_MATRIX.md" in export_script, "export script missing verification matrix")
    require(
        'copy_path "scripts/check_public_verification_matrix.sh"' in export_script,
        "export script missing verification matrix checker copy",
    )
    require("check_public_verification_matrix.sh" in read(private_smoke_path), "private smoke missing verification matrix check")
    require("check_public_verification_matrix.sh" in read(release_gate_path), "release gate missing verification matrix check")
    require("docs/public/PUBLIC_VERIFICATION_MATRIX.md" in read(release_gate_path), "release gate missing verification matrix required file")

private_runtime_markers = [
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
    "vl" + "ess",
]
lowered = text.lower()
for marker in private_runtime_markers:
    require(re.search(marker, lowered) is None, f"private runtime marker leaked into verification matrix: {marker}")

if errors:
    print("public verification matrix check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"public verification matrix check ok: rows={row_count}")
PY
