# SLO Canary Gate Evidence

DriveDesk includes a public-safe canary gate drill that proves a release
candidate can be blocked before promotion when it violates service objectives.

## Command

```bash
bash scripts/check_public_slo_canary_gate.sh
```

## What The Drill Does

The script creates temporary synthetic metrics and simulates this flow:

```text
stable release metrics inside SLO
        |
        v
candidate release evaluated as canary
        |
        v
availability, latency, and burn-rate violations detected
        |
        v
promotion is blocked and stable release remains active
```

The drill verifies:

- the stable baseline is inside SLO;
- the candidate canary is evaluated;
- availability degradation is detected;
- p95 latency degradation is detected;
- error budget burn is detected;
- promotion is blocked;
- a `release.canary_gate.blocked` audit event is recorded;
- synthetic metric and decision hashes are recorded;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "drill": "public_synthetic_slo_canary_gate",
  "data_profile": "synthetic_fake_data",
  "gate_model": "slo_canary_promotion_gate",
  "checks": {
    "stable_baseline_within_slo": true,
    "candidate_canary_evaluated": true,
    "availability_violation_detected": true,
    "latency_violation_detected": true,
    "burn_rate_violation_detected": true,
    "promotion_blocked": true,
    "production_data_touched": false
  },
  "decision": {
    "event_type": "release.canary_gate.blocked",
    "promote": false
  }
}
```

## Redaction Boundary

The public drill uses temporary local files and synthetic fake data. It does
not include private deployment paths, hostnames, addresses, credentials, raw
logs, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/slo-canary-gate.sanitized.json
```

## Why This Matters

Rollback proves recovery after a bad release. A canary gate proves release
control before the bad release becomes the active version. This is the
engineering difference between "we can clean up later" and "we can stop a bad
candidate at the promotion boundary."
