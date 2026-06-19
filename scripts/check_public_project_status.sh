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
    "Platform tour",
    "Business event, Control Tower, workflow, Adapter Studio, outbox, incidents, and proof",
    "PLATFORM_TOUR.md",
    "bash scripts/check_public_platform_tour.sh",
    "SYSTEM_REVIEW_PATH.md",
    "bash scripts/check_public_system_review_path.sh",
    "REVIEWER_QUICKSTART.md",
    "bash scripts/check_public_reviewer_quickstart.sh",
    "API contract",
    "Client SDK",
    "typed file-import and Bitrix-style CRM adapter operation helpers",
    "examples/python/demo_adapter_operation_plan.py",
    "examples/js/demo-adapter-operation-plan.mjs",
    "Auth and tenant boundary",
    "Business workflow",
    "Business scenario replay",
    "reusable workflow scenarios",
    "end-to-end workflow-to-proof scenario",
    "Integration hub",
    "provider connector guide",
    "adapter developer guide",
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
    "GET /demo/connector-fixture-replay",
    "GET /demo/business-intake-pipeline",
    "GET /demo/business-scenario-replay",
    "PUBLIC_EXPORT_MANIFEST.md",
    "docs/public/SANITIZED_EVIDENCE.md",
    "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/BUSINESS_INTAKE_PIPELINE.md",
    "docs/public/BUSINESS_SCENARIO_REPLAY.md",
    "docs/public/OBSERVABILITY_PROOF.md",
    "docs/public/evidence/observability-proof.sanitized.json",
    "docs/public/ALERT_ROUTING_EVIDENCE.md",
    "docs/public/evidence/alert-routing.sanitized.json",
    "docs/public/INCIDENT_RESPONSE_DEMO.md",
    "docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md",
    "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
    "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
    "bash scripts/check_public_provider_connector_guide.sh",
    "bash scripts/check_public_adapter_developer_guide.sh",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/check_public_project_status.sh",
    "bash scripts/check_public_technical_capability_map.sh",
    "bash scripts/check_public_observability_proof.sh",
    "bash scripts/check_public_alert_routing.sh",
    "bash scripts/check_public_engineering_proof.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_business_intake_pipeline.sh",
    "bash scripts/check_public_business_scenario_replay.sh",
    "bash scripts/check_public_export_secrets.sh",
]:
    require(token in text, f"project status missing {token}")

target_paths = [
    "docs/public/SYSTEM_REVIEW_PATH.md",
    "docs/public/PLATFORM_TOUR.md",
    "docs/public/REVIEWER_QUICKSTART.md",
    "docs/public/ENGINEERING_REVIEW_GUIDE.md",
    "docs/public/API_BACKED_DEMO.md",
    "docs/public/CLIENT_SDK.md",
    "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
    "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
    "docs/public/AUTH_FOUNDATION.md",
    "docs/public/TENANT_ISOLATION.md",
    "docs/public/PLATFORM_ADMIN.md",
    "docs/public/BUSINESS_RECORDS.md",
    "docs/public/WORKFLOW_DEMO.md",
    "docs/public/BUSINESS_SCENARIO_REPLAY.md",
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
    require("SYSTEM_REVIEW_PATH.md" in read(doc_path), f"{label} missing SYSTEM_REVIEW_PATH.md")
    require("PLATFORM_TOUR.md" in read(doc_path), f"{label} missing PLATFORM_TOUR.md")
    require("REVIEWER_QUICKSTART.md" in read(doc_path), f"{label} missing REVIEWER_QUICKSTART.md")

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
    require("SYSTEM_REVIEW_PATH.md" in read(root_readme_path), "public README missing system review path")
    require("PLATFORM_TOUR.md" in read(root_readme_path), "public README missing platform tour")
    require("REVIEWER_QUICKSTART.md" in read(root_readme_path), "public README missing reviewer quickstart")
    require("PROJECT_STATUS.md" in read(index_path), "public Pages root missing project status")
    require("SYSTEM_REVIEW_PATH.md" in read(index_path), "public Pages root missing system review path")
    require("PLATFORM_TOUR.md" in read(index_path), "public Pages root missing platform tour")
    require("REVIEWER_QUICKSTART.md" in read(index_path), "public Pages root missing reviewer quickstart")
    require(
        "check_public_system_review_path.sh" in read(public_smoke_path),
        "public smoke missing system review path check",
    )
    require(
        "check_public_platform_tour.sh" in read(public_smoke_path),
        "public smoke missing platform tour check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(public_smoke_path),
        "public smoke missing reviewer quickstart check",
    )
    require(
        "check_public_project_status.sh" in read(public_smoke_path),
        "public smoke missing project status check",
    )
    require(
        "check_public_provider_connector_guide.sh" in read(public_smoke_path),
        "public smoke missing provider connector guide check",
    )
    require(
        "check_public_adapter_developer_guide.sh" in read(public_smoke_path),
        "public smoke missing adapter developer guide check",
    )
else:
    export_script = read(export_script_path)
    require("SYSTEM_REVIEW_PATH.md" in export_script, "export script missing system review path")
    require("PLATFORM_TOUR.md" in export_script, "export script missing platform tour")
    require("PROJECT_STATUS.md" in export_script, "export script missing project status")
    require("REVIEWER_QUICKSTART.md" in export_script, "export script missing reviewer quickstart")
    require("PROVIDER_CONNECTOR_GUIDE.md" in export_script, "export script missing provider connector guide")
    require("ADAPTER_DEVELOPER_GUIDE.md" in export_script, "export script missing adapter developer guide")
    require(
        'copy_path "scripts/check_public_system_review_path.sh"' in export_script,
        "export script missing system review path check copy",
    )
    require(
        'copy_path "scripts/check_public_platform_tour.sh"' in export_script,
        "export script missing platform tour check copy",
    )
    require(
        'copy_path "scripts/check_public_reviewer_quickstart.sh"' in export_script,
        "export script missing reviewer quickstart check copy",
    )
    require(
        'copy_path "scripts/check_public_project_status.sh"' in export_script,
        "export script missing project status check copy",
    )
    require(
        'copy_path "scripts/check_public_provider_connector_guide.sh"' in export_script,
        "export script missing provider connector guide check copy",
    )
    require(
        'copy_path "scripts/check_public_adapter_developer_guide.sh"' in export_script,
        "export script missing adapter developer guide check copy",
    )
    require(
        "check_public_system_review_path.sh" in read(private_smoke_path),
        "private smoke missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(private_smoke_path),
        "private smoke missing reviewer quickstart check",
    )
    require(
        "check_public_project_status.sh" in read(private_smoke_path),
        "private smoke missing project status check",
    )
    require(
        "check_public_provider_connector_guide.sh" in read(private_smoke_path),
        "private smoke missing provider connector guide check",
    )
    require(
        "check_public_adapter_developer_guide.sh" in read(private_smoke_path),
        "private smoke missing adapter developer guide check",
    )
    require(
        "check_public_system_review_path.sh" in read(release_gate_path),
        "release gate missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(release_gate_path),
        "release gate missing reviewer quickstart check",
    )
    require(
        "check_public_project_status.sh" in read(release_gate_path),
        "release gate missing project status check",
    )
    require(
        "check_public_provider_connector_guide.sh" in read(release_gate_path),
        "release gate missing provider connector guide check",
    )
    require(
        "check_public_adapter_developer_guide.sh" in read(release_gate_path),
        "release gate missing adapter developer guide check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_system_review_path.sh" in read(public_smoke_path),
        "public smoke missing system review path check",
    )
    require(
        "check_public_reviewer_quickstart.sh" in read(public_smoke_path),
        "public smoke missing reviewer quickstart check",
    )
    require(
        "check_public_project_status.sh" in read(public_smoke_path),
        "public smoke missing project status check",
    )
    require(
        "check_public_provider_connector_guide.sh" in read(public_smoke_path),
        "public smoke missing provider connector guide check",
    )
    require(
        "check_public_adapter_developer_guide.sh" in read(public_smoke_path),
        "public smoke missing adapter developer guide check",
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
