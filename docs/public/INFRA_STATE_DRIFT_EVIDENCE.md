# Infrastructure State Drift Evidence

DriveDesk includes a public-safe infrastructure state drift check for the
OpenTofu layer. The previous OpenTofu evidence describes the desired
infrastructure contract. This layer compares that desired state with a
synthetic observed state and records the plan-only response.

## Command

```bash
bash scripts/check_public_infra_state_drift.sh
```

## What The Check Does

The check validates the synthetic infrastructure drift loop:

```text
OpenTofu desired state
    |
synthetic observed state
    |
component-by-component comparison
    |
drift evidence
    |
plan-only remediation decision
```

The check verifies:

- desired state is recorded;
- observed state is recorded;
- the OpenTofu plan layer is referenced;
- component inventories match;
- state backend encryption and locking boundaries are preserved;
- secret values remain excluded;
- observability and backup storage drift is detected;
- in-sync components are recorded;
- the decision is plan-only and does not apply anything;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_infra_state_drift",
  "data_profile": "synthetic_fake_data",
  "drift_model": "opentofu_desired_vs_observed_state",
  "drift": {
    "detected": true,
    "drifted_components": ["observability", "backup_storage"]
  },
  "checks": {
    "state_backend_boundary_preserved": true,
    "secret_values_excluded": true,
    "plan_only_no_apply": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drift evidence uses synthetic desired and observed state. It does not
include real state files, backend configuration, cloud account IDs, live
endpoints, addresses, credentials, raw logs, runtime connection values, or
production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/infra-state-drift.sanitized.json
```

The source snapshots are stored at:

```text
infra/opentofu/state/desired-state.sanitized.json
infra/opentofu/state/observed-state.sanitized.json
infra/opentofu/state/drift-summary.sanitized.json
```

## Why This Matters

Infrastructure as code is useful only when desired state can be compared with
observed state. This evidence shows the operational loop after an OpenTofu plan:
compare, detect drift, preserve state and secret boundaries, and plan a safe
reviewed remediation without claiming public infrastructure exists.
