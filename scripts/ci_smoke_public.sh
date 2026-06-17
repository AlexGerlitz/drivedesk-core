#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
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

"$PYTHON_BIN" -m compileall -q apps packages tests
"$PYTHON_BIN" -m pytest -q
bash scripts/check_public_export_secrets.sh

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker compose -f infra/docker/docker-compose.foundation.yml config --quiet
  if [[ "${CI_DOCKER_BUILD:-0}" == "1" ]]; then
    docker build --file infra/docker/Dockerfile.drivedesk --tag drivedesk-core-public-ci:smoke .
  fi
else
  echo "docker not available; skipped docker compose config check"
fi
