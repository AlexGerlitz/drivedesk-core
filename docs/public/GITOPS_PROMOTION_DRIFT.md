# GitOps Promotion And Drift Evidence

DriveDesk includes a public-safe image promotion and drift-detection drill for
the GitOps delivery model.

## Command

```bash
bash scripts/check_public_gitops_promotion_drift.sh
```

## What The Check Does

The check validates the synthetic delivery evidence:

```text
candidate image tag
    |
    v
promotion gates
    |
    v
build -> staging -> canary -> production desired state
    |
    v
desired tag compared with observed tag
```

The check verifies:

- candidate image tag is recorded;
- previous image tag is recorded for rollback;
- stage value files are referenced;
- promotion gates are referenced;
- desired state is recorded for all stages;
- observed state is recorded for all stages;
- production drift is detected;
- build, staging, and canary are still synced;
- environment values remain public-safe;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_gitops_promotion_drift",
  "data_profile": "synthetic_demo_data",
  "delivery_model": "argocd_gitops_image_promotion",
  "checks": {
    "candidate_image_recorded": true,
    "rollback_tag_recorded": true,
    "drift_detected": true,
    "out_of_sync_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drill uses synthetic tags and synthetic observed state. It does not
include live cluster endpoints, server-specific addresses, raw logs, runtime
connection values, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/gitops-promotion-drift.sanitized.json
```

## Why This Matters

GitOps is useful only if desired state can be promoted and compared with
observed state. This drill shows the operational loop: promote a candidate tag,
record rollback context, detect drift, and keep evidence public-safe.
