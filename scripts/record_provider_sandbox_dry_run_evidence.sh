#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MODE="${MODE:-execute-read-only}"
TRANSPORT="${TRANSPORT:-fake}"
OUTPUT="${OUTPUT:-$ROOT/data/provider-sandbox-dry-runs/latest.sanitized.json}"
PYTHON_BIN="${PYTHON_BIN:-}"

cd "$ROOT"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi
fi

export PYTHONPATH="$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"

case "$MODE" in
  plan-only)
    "$PYTHON_BIN" scripts/run_provider_sandbox_dry_run.py \
      --plan-only \
      --output "$OUTPUT"
    "$PYTHON_BIN" scripts/check_provider_sandbox_dry_run_evidence.py "$OUTPUT"
    ;;
  execute-read-only)
    "$PYTHON_BIN" scripts/run_provider_sandbox_dry_run.py \
      --execute-read-only \
      --transport "$TRANSPORT" \
      --output "$OUTPUT"
    "$PYTHON_BIN" scripts/check_provider_sandbox_dry_run_evidence.py "$OUTPUT" --require-completed
    ;;
  *)
    echo "unsupported MODE: $MODE" >&2
    exit 2
    ;;
esac

echo "provider sandbox dry-run evidence recorded: $OUTPUT"
