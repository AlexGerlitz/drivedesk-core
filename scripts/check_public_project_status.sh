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
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
roadmap_path = root / "docs/public/ROADMAP.md"
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


require(status_path.is_file(), "missing docs/public/PROJECT_STATUS.md")
text = read(status_path)

for token in [
    "Project Status",
    "Snapshot",
    "Current Limits",
    "Next Engineering Work",
    "Verification",
    "Public entrypoint",
    "API contract",
    "Client SDK",
    "typed adapter operation helpers",
    "examples/python/demo_adapter_operation_plan.py",
    "examples/js/demo-adapter-operation-plan.mjs",
    "Auth and tenant boundary",
    "Business workflow",
    "reusable workflow scenarios",
    "Integration hub",
    "operation scenarios",
    "typed SDK operation plans",
    "Recovery and release safety",
    "GitOps and IaC",
    "Evidence boundary",
    "Capability map",
    "Observability proof",
    "Alert routing",
    "Incident response",
    "synthetic data",
    "sanitized evidence",
    "docs/openapi.json",
    "GET /demo/public",
    "PUBLIC_EXPORT_MANIFEST.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/evidence/observability-proof.sanitized.json",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/evidence/alert-routing.sanitized.json",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/check_public_project_status.sh",
    "bash scripts/check_public_technical_capability_map.sh",
    "bash scripts/check_public_observability_proof.sh",
    "bash scripts/check_public_alert_routing.sh",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_export_secrets.sh",
]:
    require(token in text, f"project status missing {token}")

target_paths = [
    "docs/public/ENGINEERING_REVIEW_GUIDE.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/AUTH_FOUNDATION.md",
    "docs/public/TENANT_ISOLATION.md",
    "docs/public/PLATFORM_ADMIN.md",
    "docs/public/BUSINESS_RECORDS.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/WORKFLOW_RULES.md",
    "docs/public/WORKFLOW_ACTION_RUNS.md",
    "docs/public/INTEGRATION_ADAPTER_CATALOG.md",
    "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
    "docs/public/INTEGRATION_RECONCILIATION.md",
    "docs/public/BACKUP_RESTORE_EVIDENCE.md",
    "docs/public/RELEASE_ROLLBACK_EVIDENCE.md",
    "docs/public/SLO_CANARY_GATE_EVIDENCE.md",
    "docs/public/STAGED_PROMOTION_EVIDENCE.md",
    "docs/public/GITOPS_DELIVERY.md",
    "docs/public/GITOPS_IMAGE_AUTOMATION.md",
    "docs/public/OPENTOFU_PLAN_EVIDENCE.md",
    "docs/public/INFRA_STATE_DRIFT_EVIDENCE.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/ROADMAP.md",
]
for path in target_paths:
    require(path in text, f"project status missing target path {path}")
    require((root / path).is_file(), f"project status target missing: {path}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (review_guide_path, "review guide"),
    (capability_map_path, "technical capability map"),
    (roadmap_path, "roadmap"),
]:
    require("PROJECT_STATUS.md" in read(doc_path), f"{label} missing PROJECT_STATUS.md")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for path in [
        "README.md",
        "index.html",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_export_secrets.sh",
    ]:
        require((root / path).is_file(), f"public export target missing: {path}")
    require("PROJECT_STATUS.md" in read(root_readme_path), "public README missing project status")
    require("PROJECT_STATUS.md" in read(index_path), "public Pages root missing project status")
    require(
        "check_public_project_status.sh" in read(public_smoke_path),
        "public smoke missing project status check",
    )
else:
    export_script = read(export_script_path)
    require("PROJECT_STATUS.md" in export_script, "export script missing project status")
    require(
        'copy_path "scripts/check_public_project_status.sh"' in export_script,
        "export script missing project status check copy",
    )
    require(
        "check_public_project_status.sh" in read(private_smoke_path),
        "private smoke missing project status check",
    )
    require(
        "check_public_project_status.sh" in read(release_gate_path),
        "release gate missing project status check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_project_status.sh" in read(public_smoke_path),
        "public smoke missing project status check",
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
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into project status: {pattern}")

if errors:
    for error in errors:
        print(f"project_status_error={error}", file=sys.stderr)
    raise SystemExit("public project status check failed")

print("public project status check ok: docs/public/PROJECT_STATUS.md")
PY
