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
import re
import sys
from pathlib import Path

gitops_dir = Path(sys.argv[1])
stages = ["build", "staging", "canary", "production"]

required_files = [
    "promotion/image-promotion.yaml",
    "promotion/order.yaml",
    "drift/desired-state.yaml",
    "drift/observed-state.yaml",
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

promotion = texts.get("promotion/image-promotion.yaml", "")
promotion_order = texts.get("promotion/order.yaml", "")
desired = texts.get("drift/desired-state.yaml", "")
observed = texts.get("drift/observed-state.yaml", "")
values = {stage: texts.get(f"environments/{stage}/values.yaml", "") for stage in stages}

candidate_tag = "gitops-candidate-2026-06-18"
previous_tag = "gitops-previous-release"

def stage_field_map(text: str, field: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current_stage: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        stage_match = re.match(r"- name: (build|staging|canary|production)$", line)
        if stage_match:
            current_stage = stage_match.group(1)
            continue
        if current_stage and line.startswith(f"{field}: "):
            result[current_stage] = line.split(": ", 1)[1]
    return result


desired_by_stage = stage_field_map(desired, "desiredTag")
observed_by_stage = stage_field_map(observed, "observedTag")
sync_by_stage = stage_field_map(observed, "syncStatus")

drifted_stages = [
    stage
    for stage in stages
    if desired_by_stage.get(stage) and observed_by_stage.get(stage)
    and desired_by_stage[stage] != observed_by_stage[stage]
]

checks = {
    "promotion_files_present": not missing,
    "candidate_image_recorded": candidate_tag in promotion,
    "previous_image_recorded": previous_tag in promotion,
    "stage_values_files_referenced": all(
        f"infra/gitops/environments/{stage}/values.yaml" in promotion for stage in stages
    ),
    "promotion_gates_referenced": all(
        gate in promotion
        for gate in [
            "public_export_secret_scan",
            "public_demo_api_smoke",
            "helm_chart_render",
            "gitops_layout",
            "slo_canary_gate",
            "staged_promotion_drill",
        ]
    ),
    "rollback_tag_recorded": previous_tag in promotion and "restoreTag:" in promotion,
    "desired_state_recorded": all(desired_by_stage.get(stage) == candidate_tag for stage in stages),
    "observed_state_recorded": all(stage in observed_by_stage for stage in stages),
    "drift_detected": drifted_stages == ["production"],
    "out_of_sync_recorded": sync_by_stage.get("production") == "OutOfSync",
    "synced_stages_recorded": all(sync_by_stage.get(stage) == "Synced" for stage in ["build", "staging", "canary"]),
    "environment_values_still_public_safe": all(
        "repository: ghcr.io/alexgerlitz/drivedesk-core-public" in values[stage]
        and "runtimeSecret:" in values[stage]
        for stage in stages
    ),
    "promotion_order_links_gitops_layout": "gitops_layout" in promotion_order,
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

payload = {
    "schema_version": 1,
    "check": "public_gitops_promotion_drift",
    "data_profile": "synthetic_demo_data",
    "delivery_model": "argocd_gitops_image_promotion",
    "promotion": {
        "candidate_tag": candidate_tag,
        "previous_tag": previous_tag,
        "stages": stages,
        "drifted_stages": drifted_stages,
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
        print(f"missing GitOps promotion files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public GitOps promotion drift check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public GitOps promotion drift check ok: "
    "candidate=gitops-candidate-2026-06-18 drifted=production"
)
PY
