# Private Infrastructure Scheduled Validation

DriveDesk includes a public-safe scheduled validation evidence layer. It records
that private infrastructure validation is expected to run repeatedly, with a
daily schedule, manual dispatch fallback, missed-run guard, and sanitized
evidence boundaries.

## Command

```bash
bash scripts/check_public_private_infra_scheduled_validation.sh
```

## Workflow

The public-safe workflow is stored at:

```text
.github/workflows/scheduled-validation.yml
```

It runs:

- `scripts/check_public_private_infra_scheduled_validation.sh`;
- `scripts/check_public_private_infra_post_remediation_drift_refresh.sh`;
- `scripts/check_public_export_secrets.sh` when the public export helper is
  present, otherwise `scripts/check_secrets.sh` in the private repository.

## What The Check Does

The check validates the recurring validation loop:

```text
daily schedule
    |
public-safe validation checker
    |
post-remediation drift refresh recheck
    |
secret boundary recheck
    |
missed-run guard
    |
sanitized evidence
```

The check verifies:

- the scheduled validation contract is present;
- the GitHub Actions workflow has both `schedule` and `workflow_dispatch`;
- the cron expression is recorded in public-safe evidence;
- the scheduled checker runs from the workflow;
- post-remediation drift refresh is rechecked;
- public/private secret boundary is rechecked with the scanner available in
  that checkout;
- sample successful runs are recorded;
- missed-run guard and investigation route are recorded;
- the scheduled validation is read-only;
- no OpenTofu apply, no GitOps sync, no runtime mutation, no service restart,
  and no production apply are recorded;
- public evidence excludes addresses, credentials, raw logs, request bodies,
  private paths, and production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_private_infra_scheduled_validation",
  "schedule_model": "recurring_private_infra_validation",
  "checks": {
    "workflow_schedule_present": true,
    "scheduled_checker_runs": true,
    "missed_run_guard_recorded": true,
    "read_only_schedule_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public scheduled validation evidence uses only sanitized summaries. It does
not include live endpoints, server-specific paths, hostnames, network
addresses, credentials, raw logs, request bodies, private runtime connection
values, or production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/private-infra-scheduled-validation.sanitized.json
```

The public-safe scheduled validation contract is stored at:

```text
infra/state-validation/private-infra-scheduled-validation.sanitized.json
```

## Why This Matters

A one-time validation can go stale. Scheduled validation turns the same
engineering discipline into an operational habit: the system is checked
regularly, missed checks have an escalation path, and a clean drift state is
kept current instead of assumed.
