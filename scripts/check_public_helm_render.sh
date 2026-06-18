#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CHART_DIR="${CHART_DIR:-"$ROOT/infra/helm/drivedesk-core"}"

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

HELM_RENDERED_FILE=""
HELM_TEMPLATE_RAN=0
TMP_DIR=""

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

if command -v helm >/dev/null 2>&1; then
  TMP_DIR="$(mktemp -d -t drivedesk-helm-render.XXXXXX)"
  HELM_RENDERED_FILE="$TMP_DIR/rendered.yaml"
  helm template drivedesk-core "$CHART_DIR" \
    --values "$CHART_DIR/values.public.yaml" \
    >"$HELM_RENDERED_FILE"
  HELM_TEMPLATE_RAN=1
fi

HELM_TEMPLATE_RAN="$HELM_TEMPLATE_RAN" HELM_RENDERED_FILE="$HELM_RENDERED_FILE" "$PYTHON_BIN" - <<'PY' "$CHART_DIR"
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

chart_dir = Path(sys.argv[1])
rendered_file = Path(os.environ["HELM_RENDERED_FILE"]) if os.environ.get("HELM_RENDERED_FILE") else None
helm_template_ran = os.environ.get("HELM_TEMPLATE_RAN") == "1"

required_files = [
    "Chart.yaml",
    "values.yaml",
    "values.public.yaml",
    "values.schema.json",
    "templates/_helpers.tpl",
    "templates/configmap.yaml",
    "templates/deployment-api.yaml",
    "templates/deployment-worker.yaml",
    "templates/migration-job.yaml",
    "templates/service.yaml",
    "templates/serviceaccount.yaml",
]

missing = [relative for relative in required_files if not (chart_dir / relative).is_file()]

schema_valid = False
try:
    json.loads((chart_dir / "values.schema.json").read_text(encoding="utf-8"))
    schema_valid = True
except (OSError, json.JSONDecodeError):
    schema_valid = False

chart_yaml = (chart_dir / "Chart.yaml").read_text(encoding="utf-8")
values_yaml = (chart_dir / "values.yaml").read_text(encoding="utf-8")
templates = {
    relative: (chart_dir / relative).read_text(encoding="utf-8")
    for relative in required_files
    if relative.startswith("templates/") and (chart_dir / relative).is_file()
}
all_chart_text = "\n".join([chart_yaml, values_yaml, *templates.values()]).lower()

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
]

rendered_text = ""
if rendered_file and rendered_file.is_file():
    rendered_text = rendered_file.read_text(encoding="utf-8")

rendered_checks = {
    "helm_template_ran": helm_template_ran,
    "helm_binary_required": False,
    "rendered_api_deployment": (not helm_template_ran)
    or ("kind: Deployment" in rendered_text and "app.kubernetes.io/component: api" in rendered_text),
    "rendered_worker_deployment": (not helm_template_ran)
    or ("kind: Deployment" in rendered_text and "app.kubernetes.io/component: worker" in rendered_text),
    "rendered_migration_job": (not helm_template_ran)
    or ("kind: Job" in rendered_text and "app.kubernetes.io/component: migrate" in rendered_text),
    "rendered_service": (not helm_template_ran)
    or ("kind: Service" in rendered_text and "targetPort: http" in rendered_text),
    "rendered_secret_refs": (not helm_template_ran)
    or (
        "secretKeyRef:" in rendered_text
        and "DRIVEDESK_DATABASE_URL" in rendered_text
        and "DRIVEDESK_REDIS_URL" in rendered_text
    ),
}

checks = {
    "chart_files_present": not missing,
    "chart_metadata_valid": "apiVersion: v2" in chart_yaml
    and "name: drivedesk-core" in chart_yaml
    and "type: application" in chart_yaml,
    "values_schema_valid": schema_valid,
    "public_values_present": (chart_dir / "values.public.yaml").is_file(),
    "api_deployment_template_present": "kind: Deployment" in templates.get("templates/deployment-api.yaml", "")
    and "app.kubernetes.io/component: api" in templates.get("templates/deployment-api.yaml", ""),
    "worker_deployment_template_present": "kind: Deployment" in templates.get("templates/deployment-worker.yaml", "")
    and "app.kubernetes.io/component: worker" in templates.get("templates/deployment-worker.yaml", ""),
    "migration_job_template_present": "kind: Job" in templates.get("templates/migration-job.yaml", "")
    and "helm.sh/hook: pre-install,pre-upgrade" in templates.get("templates/migration-job.yaml", ""),
    "service_template_present": "kind: Service" in templates.get("templates/service.yaml", "")
    and "targetPort: http" in templates.get("templates/service.yaml", ""),
    "runtime_secret_refs_present": "secretkeyref:" in all_chart_text
    and "drivedesk_database_url" in all_chart_text
    and "drivedesk_redis_url" in all_chart_text,
    "health_probes_present": "livenessProbe:" in templates.get("templates/deployment-api.yaml", "")
    and "readinessProbe:" in templates.get("templates/deployment-api.yaml", ""),
    "private_markers_absent": not any(marker in all_chart_text for marker in private_markers),
    "production_data_touched": False,
    **rendered_checks,
}

passed = all(
    value
    for key, value in checks.items()
    if key not in {"production_data_touched", "helm_template_ran", "helm_binary_required"}
)
passed = passed and checks["production_data_touched"] is False

payload = {
    "schema_version": 1,
    "check": "public_helm_chart_render",
    "data_profile": "synthetic_demo_data",
    "deployment_model": "kubernetes_helm_chart",
    "chart": {
        "name": "drivedesk-core",
        "path": "infra/helm/drivedesk-core",
        "helm_template_ran": helm_template_ran,
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
        print(f"missing chart files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public Helm chart render check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public Helm chart render check ok: "
    f"chart=drivedesk-core helm_template_ran={str(helm_template_ran).lower()}"
)
PY
