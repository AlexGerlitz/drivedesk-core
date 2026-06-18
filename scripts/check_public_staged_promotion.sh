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

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path


RELEASE_ID = "candidate-2026-06-18-safe"


def _write_json(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage_passed(stage: dict[str, object]) -> bool:
    checks = stage.get("checks", {})
    return isinstance(checks, dict) and all(bool(value) for value in checks.values())


with tempfile.TemporaryDirectory(prefix="drivedesk-public-staged-promotion-") as temp_dir:
    root = Path(temp_dir)
    started_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    build_manifest = {
        "release_id": RELEASE_ID,
        "data_profile": "synthetic_fake_data",
        "source_revision": "public-synthetic-revision",
        "artifact_type": "container_image",
        "sbom_attached": True,
        "image_scan_passed": True,
        "secret_scan_passed": True,
    }
    build_hash = _write_json(root / "artifacts" / "build-manifest.json", build_manifest)

    stages = [
        {
            "name": "build",
            "status": "passed",
            "checks": {
                "compile_smoke_passed": True,
                "pytest_passed": True,
                "secret_scan_passed": True,
                "image_scan_passed": True,
                "sbom_attached": True,
            },
        },
        {
            "name": "staging",
            "status": "passed",
            "checks": {
                "api_health_passed": True,
                "public_demo_smoke_passed": True,
                "backup_restore_drill_passed": True,
                "release_rollback_drill_passed": True,
            },
        },
        {
            "name": "canary",
            "status": "passed",
            "checks": {
                "slo_canary_gate_passed": True,
                "availability_within_slo": True,
                "p95_latency_within_slo": True,
                "error_budget_burn_within_limit": True,
            },
        },
        {
            "name": "production",
            "status": "promoted",
            "checks": {
                "manual_approval_recorded": True,
                "rollback_plan_attached": True,
                "post_promotion_monitoring_required": True,
                "active_release_updated": True,
            },
        },
    ]

    approval = {
        "release_id": RELEASE_ID,
        "approval_type": "synthetic_release_manager_approval",
        "approved_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "approver_role": "release_manager",
        "reason": "all public-safe gates passed",
        "production_data_touched": False,
    }
    approval_hash = _write_json(root / "approvals" / "production-approval.json", approval)

    history = {
        "release_id": RELEASE_ID,
        "promotion_model": "build_staging_canary_production",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "stages": stages,
        "approval_hash_recorded": len(approval_hash) == 64,
        "build_hash_recorded": len(build_hash) == 64,
        "data_profile": "synthetic_fake_data",
        "production_data_touched": False,
    }
    history_hash = _write_json(root / "history" / "promotion-history.json", history)

    audit_event = {
        "event_type": "release.staged_promotion.completed",
        "release_id": RELEASE_ID,
        "promotion_model": "build_staging_canary_production",
        "recorded_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "active_stage": "production",
        "production_data_touched": False,
    }
    audit_hash = _write_json(root / "audit" / "staged-promotion.json", audit_event)

    stage_results = {str(stage["name"]): _stage_passed(stage) for stage in stages}
    checks = {
        "build_manifest_hash_recorded": len(build_hash) == 64,
        "build_gate_passed": stage_results["build"] is True,
        "staging_gate_passed": stage_results["staging"] is True,
        "canary_gate_passed": stage_results["canary"] is True,
        "production_approval_recorded": len(approval_hash) == 64,
        "rollback_plan_attached": stages[-1]["checks"]["rollback_plan_attached"] is True,
        "production_promotion_completed": stage_results["production"] is True,
        "promotion_history_hash_recorded": len(history_hash) == 64,
        "release_audit_event_recorded": len(audit_hash) == 64,
        "production_data_touched": False,
    }
    passed = all(value for key, value in checks.items() if key != "production_data_touched")
    passed = passed and checks["production_data_touched"] is False

    payload = {
        "schema_version": 1,
        "drill": "public_synthetic_staged_promotion",
        "data_profile": "synthetic_fake_data",
        "promotion_model": "build_staging_canary_production",
        "release_id": RELEASE_ID,
        "stages": stages,
        "checks": checks,
        "decision": {
            "event_type": "release.staged_promotion.completed",
            "promote": True,
            "active_stage": "production",
            "recommended_action": "monitor SLO burn and keep rollback plan attached",
        },
        "artifacts": {
            "build_manifest_sha256_prefix": build_hash[:16],
            "approval_sha256_prefix": approval_hash[:16],
            "promotion_history_sha256_prefix": history_hash[:16],
            "release_audit_sha256_prefix": audit_hash[:16],
        },
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
        raise SystemExit("public staged promotion drill failed")

    print(json.dumps(payload, indent=2, sort_keys=True))
    print(
        "public staged promotion drill ok: "
        f"release={RELEASE_ID} "
        "active_stage=production "
        "audit=release.staged_promotion.completed"
    )
PY
