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
map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
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


require(map_path.is_file(), "missing docs/public/TECHNICAL_CAPABILITY_MAP.md")
text = read(map_path)

for token in [
    "Technical Capability Map",
    "Capability Matrix",
    "Public review entrypoint",
    "Project status",
    "Read-only API contract",
    "Generated client SDK",
    "Auth, RBAC, and tenant boundary",
    "Audit and outbox recovery",
    "Business records and workflow automation",
    "Integration adapter model",
    "Recovery drills",
    "Observability proof",
    "Alert routing",
    "Incident response",
    "GitOps delivery",
    "OpenTofu and infra drift",
    "Sanitized evidence boundary",
    "Engineering proof contract",
    "docs/openapi.json",
    "GET /demo/public",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/ROADMAP.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/evidence/observability-proof.sanitized.json",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/evidence/alert-routing.sanitized.json",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md",
    "PUBLIC_EXPORT_MANIFEST.md",
    "docs/public/evidence/*.sanitized.json",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/check_public_project_status.sh",
    "bash scripts/check_public_pages_entrypoint.sh",
    "bash scripts/check_public_observability_proof.sh",
    "bash scripts/check_public_alert_routing.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_demo_sdk.sh",
    "bash scripts/check_public_backup_restore.sh",
    "bash scripts/check_public_release_rollback.sh",
    "bash scripts/check_public_slo_canary_gate.sh",
    "bash scripts/check_public_staged_promotion.sh",
    "bash scripts/check_public_helm_render.sh",
    "bash scripts/check_public_gitops_layout.sh",
    "bash scripts/check_public_gitops_image_automation.sh",
    "bash scripts/check_public_opentofu_plan.sh",
    "bash scripts/check_public_infra_state_drift.sh",
    "bash scripts/check_public_private_infra_scheduled_validation.sh",
    "bash scripts/check_public_private_infra_scheduled_alerting.sh",
    "bash scripts/check_public_export_secrets.sh",
    "bash scripts/check_public_engineering_proof.sh",
]:
    require(token in text, f"technical capability map missing {token}")

target_paths = [
    "docs/public/ENGINEERING_REVIEW_GUIDE.md",
    "docs/public/PROJECT_STATUS.md",
    "docs/public/ENGINEERING_PROOF.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/AUTH_FOUNDATION.md",
    "docs/public/TENANT_ISOLATION.md",
    "docs/public/PLATFORM_ADMIN.md",
    "docs/public/OUTBOX_RECOVERY.md",
    "docs/public/BUSINESS_RECORDS.md",
    "docs/public/BUSINESS_RECORD_LIFECYCLE.md",
    "docs/public/WORKFLOW_RULES.md",
    "docs/public/WORKFLOW_ACTION_RUNS.md",
    "docs/public/INTEGRATION_ADAPTER_CATALOG.md",
    "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
    "docs/public/INTEGRATION_RECONCILIATION.md",
    "docs/public/BACKUP_RESTORE_EVIDENCE.md",
    "docs/public/RELEASE_ROLLBACK_EVIDENCE.md",
    "docs/public/SLO_CANARY_GATE_EVIDENCE.md",
    "docs/public/STAGED_PROMOTION_EVIDENCE.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/HELM_CHART.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/GITOPS_IMAGE_AUTOMATION.md",
    "docs/public/GITOPS_DRIFT_REMEDIATION.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/public/INFRA_STATE_DRIFT_EVIDENCE.md",
    "docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md",
    "docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/ROADMAP.md",
]
for path in target_paths:
    require(path in text, f"technical capability map missing target path {path}")
    require((root / path).is_file(), f"technical capability target missing: {path}")

require("TECHNICAL_CAPABILITY_MAP.md" in read(docs_readme_path), "docs/public README missing capability map")
require("TECHNICAL_CAPABILITY_MAP.md" in read(review_guide_path), "review guide missing capability map")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for path in [
        "index.html",
        "README.md",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_export_secrets.sh",
    ]:
        require((root / path).is_file(), f"public export target missing: {path}")
    require("TECHNICAL_CAPABILITY_MAP.md" in read(root_readme_path), "public README missing capability map")
    require("TECHNICAL_CAPABILITY_MAP.md" in read(index_path), "public Pages root missing capability map")
    require(
        "check_public_technical_capability_map.sh" in read(public_smoke_path),
        "public smoke missing capability map check",
    )
else:
    export_script = read(export_script_path)
    require("TECHNICAL_CAPABILITY_MAP.md" in export_script, "export script missing capability map")
    require(
        'copy_path "scripts/check_public_technical_capability_map.sh"' in export_script,
        "export script missing capability map check copy",
    )
    require(
        "check_public_technical_capability_map.sh" in read(private_smoke_path),
        "private smoke missing capability map check",
    )
    require(
        "check_public_technical_capability_map.sh" in read(release_gate_path),
        "release gate missing capability map check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_technical_capability_map.sh" in read(public_smoke_path),
        "public smoke missing capability map check",
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
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into capability map: {pattern}")

if errors:
    for error in errors:
        print(f"technical_capability_map_error={error}", file=sys.stderr)
    raise SystemExit("public technical capability map check failed")

print("public technical capability map check ok: docs/public/TECHNICAL_CAPABILITY_MAP.md")
PY
