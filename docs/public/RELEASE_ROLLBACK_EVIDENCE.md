# Release Rollback Evidence

DriveDesk includes a public-safe rollback drill that proves the release process
has a recovery contract.

## Command

```bash
bash scripts/check_public_release_rollback.sh
```

## What The Drill Does

The script creates a temporary release directory and simulates this flow:

```text
stable release active
        |
        v
candidate release promoted
        |
        v
readiness failure detected
        |
        v
current release rolled back to stable
```

The drill verifies:

- the stable release is initially active;
- the candidate release is promoted;
- the candidate readiness failure is detected;
- rollback executes;
- the stable release is active and healthy after rollback;
- a `release.rollback.executed` audit event is recorded;
- synthetic manifest hashes are recorded;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "drill": "public_synthetic_release_rollback",
  "data_profile": "synthetic_fake_data",
  "deployment_model": "symlinked_release_directory",
  "checks": {
    "initial_stable_release_active": true,
    "candidate_release_promoted": true,
    "candidate_health_failure_detected": true,
    "rollback_executed": true,
    "stable_release_healthy_after_rollback": true,
    "rollback_audit_event_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drill uses temporary local directories and synthetic fake data. It
does not include private deployment paths, hostnames, addresses, credentials,
raw logs, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/release-rollback-drill.sanitized.json
```

## Why This Matters

Good deployments need a recovery path. This drill gives the public project a
repeatable proof that bad release detection and rollback are part of the
engineering contract, not only a runbook paragraph.
