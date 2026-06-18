# GitOps Drift Remediation Evidence

DriveDesk includes a public-safe drift remediation drill for the GitOps delivery
model. The previous layer detects drift. This layer records what the system
would do next.

## Command

```bash
bash scripts/check_public_gitops_drift_remediation.sh
```

## What The Check Does

The check validates the synthetic remediation flow:

```text
desired state
    |
observed state
    |
drift detected
    |
remediation policy
    |
plan-only decision: reconcile, rollback, or block
```

The check verifies:

- the drift input files are referenced;
- production drift is carried forward from the previous evidence layer;
- remediation policy defines reconcile, rollback, and block actions;
- production remediation requires approval;
- rollback context is attached;
- the decision is plan-only and does not apply anything to a cluster;
- `gitops.drift_remediation.planned` evidence is recorded;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_gitops_drift_remediation",
  "data_profile": "synthetic_demo_data",
  "remediation_model": "gitops_plan_only_reconcile_or_rollback",
  "checks": {
    "production_drift_carried_forward": true,
    "production_requires_approval": true,
    "plan_only_no_cluster_mutation": true,
    "rollback_option_attached": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drill uses synthetic tags, synthetic desired state, and synthetic
observed state. It does not include live cluster endpoints, server-specific
addresses, raw logs, runtime connection values, production data, or incident
payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/gitops-drift-remediation.sanitized.json
```

## Why This Matters

Drift detection is only half of the operational loop. A production-grade
delivery system also needs a safe response model: reconcile when evidence is
good, rollback when the candidate is unsafe, and block when evidence is missing.
This drill shows that response path without claiming a public cluster exists.
