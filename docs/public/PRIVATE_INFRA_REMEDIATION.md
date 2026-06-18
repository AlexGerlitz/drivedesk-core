# Private Infrastructure Remediation Plan

DriveDesk includes a public-safe private infrastructure remediation planning
layer. It records what should happen after read-only validation detects drift,
without applying infrastructure, restarting services, mutating a cluster, or
publishing private runtime details.

## Command

```bash
bash scripts/check_public_private_infra_remediation.sh
```

## What The Check Does

The check validates the safe remediation planning loop:

```text
read-only private validation
    |
infrastructure drift evidence
    |
OpenTofu and GitOps contracts
    |
operator-reviewed remediation plan
    |
rollback and postcheck gates
    |
sanitized public evidence
```

The check verifies:

- the remediation contract is present;
- private infrastructure validation evidence is referenced;
- infrastructure drift inputs are carried forward;
- OpenTofu, runtime rollout, and GitOps remediation evidence are linked;
- remediation remains plan-only;
- no public apply, cluster mutation, service restart, or runtime mutation is
  recorded;
- operator review is required before private remediation;
- each drifted component has preflight gates, postcheck gates, and rollback
  context;
- public evidence excludes addresses, credentials, raw logs, request bodies,
  private paths, and production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_private_infra_remediation_plan",
  "data_profile": "sanitized_private_staging_summary",
  "remediation_model": "private_control_plane_remediation_plan",
  "checks": {
    "validation_evidence_referenced": true,
    "drifted_components_carried_forward": true,
    "operator_review_required": true,
    "plan_only_no_apply": true,
    "rollback_attached": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public remediation evidence uses only sanitized summaries. It does not
include live endpoints, server-specific paths, hostnames, network addresses,
credentials, raw logs, request bodies, private runtime connection values, or
production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/private-infra-remediation-plan.sanitized.json
```

The public-safe remediation contract is stored at:

```text
infra/state-remediation/private-infra-remediation-plan.sanitized.json
```

## Why This Matters

Finding drift is only half of operations work. The stronger practice is to
turn a validation result into a reviewed remediation plan with preflight gates,
rollback context, and post-change evidence requirements before any private
apply happens.
