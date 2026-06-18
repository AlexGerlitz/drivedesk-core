# Staged Promotion Evidence

DriveDesk includes a public-safe staged promotion drill that proves a release
can move through build, staging, canary, and production gates with evidence.

## Command

```bash
bash scripts/check_public_staged_promotion.sh
```

## What The Drill Does

The script creates temporary synthetic release artifacts and simulates this
flow:

```text
build gate
    |
    v
staging gate
    |
    v
canary gate
    |
    v
production approval and promotion
```

The drill verifies:

- a build manifest hash is recorded;
- build checks pass;
- staging checks pass;
- canary SLO checks pass;
- production approval is recorded;
- a rollback plan is attached;
- the release is promoted to production;
- promotion history is hashed;
- a `release.staged_promotion.completed` audit event is recorded;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "drill": "public_synthetic_staged_promotion",
  "data_profile": "synthetic_fake_data",
  "promotion_model": "build_staging_canary_production",
  "checks": {
    "build_gate_passed": true,
    "staging_gate_passed": true,
    "canary_gate_passed": true,
    "production_approval_recorded": true,
    "production_promotion_completed": true,
    "promotion_history_hash_recorded": true,
    "production_data_touched": false
  },
  "decision": {
    "event_type": "release.staged_promotion.completed",
    "promote": true,
    "active_stage": "production"
  }
}
```

## Redaction Boundary

The public drill uses temporary local files and synthetic fake data. It does
not include private deployment paths, hostnames, addresses, credentials, raw
logs, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/staged-promotion.sanitized.json
```

## Why This Matters

Backup, rollback, and canary checks are individual safety mechanisms. Staged
promotion shows how those mechanisms become a release process: every gate has a
result, production promotion requires approval, and the final decision is
auditable.
