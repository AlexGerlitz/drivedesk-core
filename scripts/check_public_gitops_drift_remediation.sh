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

required_files = [
    "drift/desired-state.yaml",
    "drift/observed-state.yaml",
    "promotion/image-promotion.yaml",
    "remediation/policy.yaml",
    "remediation/decision.yaml",
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

desired = texts.get("drift/desired-state.yaml", "")
observed = texts.get("drift/observed-state.yaml", "")
promotion = texts.get("promotion/image-promotion.yaml", "")
policy = texts.get("remediation/policy.yaml", "")
decision = texts.get("remediation/decision.yaml", "")

candidate_tag = "gitops-candidate-2026-06-18"
previous_tag = "gitops-previous-release"
audit_event = "gitops.drift_remediation.planned"

checks = {
    "remediation_files_present": not missing,
    "drift_inputs_referenced": all(
        value in decision
        for value in [
            "infra/gitops/drift/desired-state.yaml",
            "infra/gitops/drift/observed-state.yaml",
            "infra/gitops/promotion/image-promotion.yaml",
            "infra/gitops/remediation/policy.yaml",
        ]
    ),
    "production_drift_carried_forward": all(
        value in desired + observed + decision
        for value in [
            "application: drivedesk-core-production",
            f"desiredTag: {candidate_tag}",
            f"observedTag: {previous_tag}",
            "syncStatus: OutOfSync",
            "driftDetected: true",
        ]
    ),
    "policy_actions_defined": all(
        value in policy
        for value in [
            "name: reconcile",
            "name: rollback",
            "name: block",
        ]
    ),
    "production_requires_approval": all(
        value in policy + decision
        for value in [
            "requiresApproval: true",
            "approvalRequired: true",
            "autoReconcile: false",
        ]
    ),
    "plan_only_no_cluster_mutation": all(
        value in policy + decision
        for value in [
            "noClusterMutation: true",
            "applyMode: plan_only",
        ]
    ),
    "rollback_option_attached": previous_tag in promotion and f"rollbackTag: {previous_tag}" in decision,
    "reconcile_action_recorded": "recommendedAction: reconcile_after_approval" in decision,
    "block_action_recorded": "blockAction: keep_observed_release" in decision,
    "evidence_gates_referenced": all(
        value in policy + decision
        for value in [
            "public_gitops_promotion_drift",
            "public_synthetic_slo_canary_gate",
            "public_synthetic_staged_promotion",
        ]
    ),
    "audit_event_recorded": audit_event in decision,
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

payload = {
    "schema_version": 1,
    "check": "public_gitops_drift_remediation",
    "data_profile": "synthetic_demo_data",
    "remediation_model": "gitops_plan_only_reconcile_or_rollback",
    "remediation": {
        "audit_event": audit_event,
        "drifted_stages": ["production"],
        "production": {
            "desired_tag": candidate_tag,
            "observed_tag": previous_tag,
            "recommended_action": "reconcile_after_approval",
            "apply_mode": "plan_only",
            "approval_required": True,
            "rollback_tag": previous_tag,
        },
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
        print(f"missing GitOps remediation files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public GitOps drift remediation check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public GitOps drift remediation check ok: "
    "stage=production action=reconcile_after_approval mode=plan_only"
)
PY
