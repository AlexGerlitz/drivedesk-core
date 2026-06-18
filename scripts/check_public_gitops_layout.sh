#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
GITOPS_DIR="${GITOPS_DIR:-"$ROOT/infra/gitops"}"

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

"$PYTHON_BIN" - <<'PY' "$GITOPS_DIR"
from __future__ import annotations

import json
import sys
from pathlib import Path

gitops_dir = Path(sys.argv[1])
stages = ["build", "staging", "canary", "production"]

required_files = [
    "README.md",
    "argocd/project.yaml",
    "promotion/order.yaml",
    *[f"argocd/app-{stage}.yaml" for stage in stages],
    *[f"environments/{stage}/values.yaml" for stage in stages],
]

missing = [relative for relative in required_files if not (gitops_dir / relative).is_file()]
texts = {
    relative: (gitops_dir / relative).read_text(encoding="utf-8")
    for relative in required_files
    if (gitops_dir / relative).is_file()
}
all_text = "\n".join(texts.values()).lower()

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
]

applications = [texts.get(f"argocd/app-{stage}.yaml", "") for stage in stages]
project = texts.get("argocd/project.yaml", "")
promotion = texts.get("promotion/order.yaml", "")
values = {stage: texts.get(f"environments/{stage}/values.yaml", "") for stage in stages}

checks = {
    "gitops_files_present": not missing,
    "argocd_project_present": "kind: AppProject" in project
    and "name: drivedesk-core" in project,
    "argocd_applications_present": all("kind: Application" in app for app in applications),
    "public_repo_source_present": all(
        "https://github.com/AlexGerlitz/drivedesk-core.git" in app for app in applications
    )
    and "https://github.com/AlexGerlitz/drivedesk-core.git" in project,
    "helm_chart_path_referenced": all("path: infra/helm/drivedesk-core" in app for app in applications)
    and "chartPath: infra/helm/drivedesk-core" in promotion,
    "environment_value_files_referenced": all(
        f"../../gitops/environments/{stage}/values.yaml" in texts.get(f"argocd/app-{stage}.yaml", "")
        for stage in stages
    ),
    "environment_overlays_present": all(f"environment: {stage}" in values[stage] for stage in stages),
    "runtime_secret_refs_present": all("runtimeSecret:" in values[stage] for stage in stages),
    "staged_promotion_order_present": all(
        f"name: {stage}" in promotion and f"application: drivedesk-core-{stage}" in promotion
        for stage in stages
    ),
    "evidence_gates_referenced": all(
        gate in promotion
        for gate in [
            "public_export_secret_scan",
            "public_demo_api_smoke",
            "backup_restore_drill",
            "release_rollback_drill",
            "slo_canary_gate",
            "staged_promotion_drill",
            "helm_chart_render",
            "gitops_layout",
        ]
    ),
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

payload = {
    "schema_version": 1,
    "check": "public_gitops_layout",
    "data_profile": "synthetic_demo_data",
    "delivery_model": "argocd_gitops",
    "gitops": {
        "path": "infra/gitops",
        "controller": "argocd",
        "chart_path": "infra/helm/drivedesk-core",
        "environments": stages,
    },
    "checks": checks,
    "redaction": {
        "paths_included": False,
        "hostnames_included": False,
        "addresses_included": False,
        "credentials_included": False,
        "raw_logs_included": False,
        "production_data_included": False,
    },
}

if not passed:
    print(json.dumps(payload, indent=2, sort_keys=True))
    if missing:
        print(f"missing GitOps files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public GitOps layout check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public GitOps layout check ok: "
    "controller=argocd stages=build,staging,canary,production"
)
PY
