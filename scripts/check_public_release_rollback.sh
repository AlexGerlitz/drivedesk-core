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


def _write_manifest(path: Path, payload: dict[str, object]) -> str:
    path.mkdir(parents=True, exist_ok=True)
    manifest_path = path / "release.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (path / "VERSION").write_text(str(payload["release_id"]) + "\n", encoding="utf-8")
    return digest


def _read_manifest(path: Path) -> dict[str, object]:
    return json.loads((path / "release.json").read_text(encoding="utf-8"))


def _switch_current(current: Path, release_path: Path) -> None:
    next_link = current.with_name("current.next")
    if next_link.exists() or next_link.is_symlink():
        next_link.unlink()
    next_link.symlink_to(release_path, target_is_directory=True)
    next_link.replace(current)


def _active_release_id(current: Path) -> str:
    return str(_read_manifest(current.resolve())["release_id"])


def _health_ok(release_path: Path) -> bool:
    checks = _read_manifest(release_path).get("checks", {})
    if not isinstance(checks, dict):
        return False
    return all(bool(value) for value in checks.values())


def _write_audit_event(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory(prefix="drivedesk-public-rollback-") as temp_dir:
    root = Path(temp_dir)
    releases = root / "releases"
    current = root / "current"
    audit_file = root / "audit" / "release-rollback.json"

    stable_release = releases / "stable-2026-06-18"
    candidate_release = releases / "candidate-2026-06-18"

    stable_hash = _write_manifest(
        stable_release,
        {
            "release_id": "stable-2026-06-18",
            "commit": "public-stable",
            "data_profile": "synthetic_fake_data",
            "schema_version": 1,
            "checks": {
                "api_health_ok": True,
                "api_ready_ok": True,
                "public_demo_contract_ok": True,
                "backup_restore_drill_ok": True,
            },
        },
    )
    candidate_hash = _write_manifest(
        candidate_release,
        {
            "release_id": "candidate-2026-06-18",
            "commit": "public-candidate",
            "data_profile": "synthetic_fake_data",
            "schema_version": 1,
            "checks": {
                "api_health_ok": True,
                "api_ready_ok": False,
                "public_demo_contract_ok": True,
                "backup_restore_drill_ok": True,
            },
        },
    )

    _switch_current(current, stable_release)
    initial_release_id = _active_release_id(current)

    _switch_current(current, candidate_release)
    candidate_promoted_id = _active_release_id(current)
    candidate_health_ok = _health_ok(current.resolve())

    rollback_started_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    if not candidate_health_ok:
        _switch_current(current, stable_release)
    rollback_finished_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    active_after_rollback = _active_release_id(current)
    stable_after_rollback_ok = _health_ok(current.resolve())

    audit_hash = _write_audit_event(
        audit_file,
        {
            "event_type": "release.rollback.executed",
            "started_at_utc": rollback_started_at,
            "finished_at_utc": rollback_finished_at,
            "from_release": candidate_promoted_id,
            "to_release": stable_release.name,
            "reason": "synthetic readiness check failed",
            "data_profile": "synthetic_fake_data",
            "production_data_touched": False,
        },
    )

    checks = {
        "initial_stable_release_active": initial_release_id == "stable-2026-06-18",
        "candidate_release_promoted": candidate_promoted_id == "candidate-2026-06-18",
        "candidate_health_failure_detected": candidate_health_ok is False,
        "rollback_executed": active_after_rollback == "stable-2026-06-18",
        "stable_release_healthy_after_rollback": stable_after_rollback_ok is True,
        "rollback_audit_event_recorded": audit_file.exists(),
        "rollback_audit_event_hash_recorded": len(audit_hash) == 64,
        "candidate_manifest_hash_recorded": len(candidate_hash) == 64,
        "stable_manifest_hash_recorded": len(stable_hash) == 64,
        "production_data_touched": False,
    }
    passed = all(value for key, value in checks.items() if key != "production_data_touched")
    passed = passed and checks["production_data_touched"] is False

    payload = {
        "schema_version": 1,
        "drill": "public_synthetic_release_rollback",
        "data_profile": "synthetic_fake_data",
        "deployment_model": "symlinked_release_directory",
        "checks": checks,
        "release_flow": {
            "initial_release": initial_release_id,
            "candidate_release": candidate_promoted_id,
            "active_after_rollback": active_after_rollback,
            "rollback_event": "release.rollback.executed",
        },
        "artifacts": {
            "stable_manifest_sha256_prefix": stable_hash[:16],
            "candidate_manifest_sha256_prefix": candidate_hash[:16],
            "rollback_audit_sha256_prefix": audit_hash[:16],
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
        raise SystemExit("public release rollback drill failed")

    print(json.dumps(payload, indent=2, sort_keys=True))
    print(
        "public release rollback drill ok: "
        f"from={candidate_promoted_id} "
        f"to={active_after_rollback} "
        f"audit=release.rollback.executed"
    )
PY
