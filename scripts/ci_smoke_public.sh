#!/usr/bin/env bash
set -euo pipefail

ROOT="${PUBLIC_EXPORT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export ROOT
cd "$ROOT"

if [[ -n "${PUBLIC_EXPORT_PYTHON:-}" && -x "$PUBLIC_EXPORT_PYTHON" ]]; then
  PYTHON_BIN="$PUBLIC_EXPORT_PYTHON"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="$(command -v python)"
fi

export PYTHONPATH="$ROOT/apps/api:$ROOT/apps/worker:$ROOT/packages/core"

"$PYTHON_BIN" -m compileall -q apps packages tests examples scripts
"$PYTHON_BIN" -m pytest -q
bash scripts/check_public_export_secrets.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/check_public_backup_restore.sh
bash scripts/check_public_release_rollback.sh
bash scripts/check_public_slo_canary_gate.sh
bash scripts/check_public_staged_promotion.sh
bash scripts/check_public_helm_render.sh
bash scripts/check_public_opentofu_plan.sh
bash scripts/check_public_infra_state_drift.sh
bash scripts/check_public_runtime_rollout.sh
bash scripts/check_public_private_infra_validation.sh
bash scripts/check_public_private_infra_remediation.sh
bash scripts/check_public_private_infra_remediation_execution.sh
bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh
bash scripts/check_public_private_infra_scheduled_validation.sh
bash scripts/check_public_private_infra_scheduled_alerting.sh
bash scripts/check_public_portfolio_70_milestone.sh
bash scripts/check_public_review_guide.sh
bash scripts/check_public_pages_entrypoint.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_gitops_layout.sh
bash scripts/check_public_gitops_image_automation.sh
bash scripts/check_public_gitops_promotion_drift.sh
bash scripts/check_public_gitops_drift_remediation.sh

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker compose -f infra/docker/docker-compose.foundation.yml config --quiet
  if [[ "${CI_DOCKER_BUILD:-0}" == "1" ]]; then
    docker build --file infra/docker/Dockerfile.drivedesk --tag drivedesk-core-public-ci:smoke .
  fi
else
  echo "docker not available; skipped docker compose config check"
fi
