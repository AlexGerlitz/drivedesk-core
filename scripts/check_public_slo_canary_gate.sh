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


SLO = {
    "availability_target_percent": 99.5,
    "max_p95_latency_ms": 400,
    "max_burn_rate": 1.0,
}


def _write_json(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluate_release(metrics: dict[str, object]) -> dict[str, object]:
    requests = int(metrics["requests"])
    errors = int(metrics["errors"])
    p95_latency_ms = int(metrics["p95_latency_ms"])
    availability_percent = round(((requests - errors) / requests) * 100, 3)
    error_budget_percent = 100 - SLO["availability_target_percent"]
    observed_error_percent = 100 - availability_percent
    burn_rate = round(observed_error_percent / error_budget_percent, 3)
    violations: list[str] = []

    if availability_percent < SLO["availability_target_percent"]:
        violations.append("availability")
    if p95_latency_ms > SLO["max_p95_latency_ms"]:
        violations.append("p95_latency")
    if burn_rate > SLO["max_burn_rate"]:
        violations.append("error_budget_burn")

    return {
        "release_id": metrics["release_id"],
        "availability_percent": availability_percent,
        "p95_latency_ms": p95_latency_ms,
        "burn_rate": burn_rate,
        "gate_passed": not violations,
        "violations": violations,
    }


with tempfile.TemporaryDirectory(prefix="drivedesk-public-slo-canary-") as temp_dir:
    root = Path(temp_dir)
    stable_metrics = {
        "release_id": "stable-2026-06-18",
        "data_profile": "synthetic_demo_data",
        "requests": 10000,
        "errors": 10,
        "p95_latency_ms": 180,
    }
    candidate_metrics = {
        "release_id": "candidate-2026-06-18",
        "data_profile": "synthetic_demo_data",
        "requests": 1000,
        "errors": 18,
        "p95_latency_ms": 620,
    }

    stable_hash = _write_json(root / "metrics" / "stable-metrics.json", stable_metrics)
    candidate_hash = _write_json(root / "metrics" / "candidate-metrics.json", candidate_metrics)

    stable = _evaluate_release(stable_metrics)
    candidate = _evaluate_release(candidate_metrics)

    event = {
        "event_type": "release.canary_gate.blocked",
        "recorded_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "stable_release": stable["release_id"],
        "candidate_release": candidate["release_id"],
        "reason": "synthetic SLO canary violation",
        "violations": candidate["violations"],
        "promote": False,
        "data_profile": "synthetic_demo_data",
        "production_data_touched": False,
    }
    event_hash = _write_json(root / "audit" / "slo-canary-gate.json", event)

    decision = {
        "event_type": "release.canary_gate.blocked",
        "promote": False,
        "recommended_action": "keep stable release active and investigate candidate",
    }
    decision_hash = _write_json(root / "decision" / "gate-decision.json", decision)

    checks = {
        "stable_baseline_within_slo": bool(stable["gate_passed"]),
        "candidate_canary_evaluated": candidate["release_id"] == "candidate-2026-06-18",
        "availability_violation_detected": "availability" in candidate["violations"],
        "latency_violation_detected": "p95_latency" in candidate["violations"],
        "burn_rate_violation_detected": "error_budget_burn" in candidate["violations"],
        "promotion_blocked": candidate["gate_passed"] is False and decision["promote"] is False,
        "gate_audit_event_recorded": len(event_hash) == 64,
        "gate_decision_hash_recorded": len(decision_hash) == 64,
        "candidate_metrics_hash_recorded": len(candidate_hash) == 64,
        "stable_metrics_hash_recorded": len(stable_hash) == 64,
        "production_data_touched": False,
    }
    passed = all(value for key, value in checks.items() if key != "production_data_touched")
    passed = passed and checks["production_data_touched"] is False

    payload = {
        "schema_version": 1,
        "drill": "public_synthetic_slo_canary_gate",
        "data_profile": "synthetic_demo_data",
        "gate_model": "slo_canary_promotion_gate",
        "slo": SLO,
        "stable": stable,
        "candidate": candidate,
        "checks": checks,
        "decision": decision,
        "artifacts": {
            "stable_metrics_sha256_prefix": stable_hash[:16],
            "candidate_metrics_sha256_prefix": candidate_hash[:16],
            "gate_audit_sha256_prefix": event_hash[:16],
            "gate_decision_sha256_prefix": decision_hash[:16],
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
        raise SystemExit("public SLO canary gate drill failed")

    print(json.dumps(payload, indent=2, sort_keys=True))
    print(
        "public SLO canary gate drill ok: "
        f"candidate={candidate['release_id']} "
        "promotion_blocked=true "
        "audit=release.canary_gate.blocked"
    )
PY
