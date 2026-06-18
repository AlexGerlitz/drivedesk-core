# Private Infrastructure Remediation Execution

DriveDesk includes a public-safe private infrastructure remediation execution
evidence layer. It records what happened after a reviewed remediation plan was
accepted, while keeping public artifacts free of live endpoints, credentials,
raw logs, private paths, request bodies, and production data.

## Command

```bash
bash scripts/check_public_private_infra_remediation_execution.sh
```

## What The Check Does

The check validates the controlled execution loop:

```text
remediation plan ready
    |
operator review recorded
    |
private staging execution summary
    |
post-remediation validation
    |
sanitized public evidence
```

The check verifies:

- the execution contract is present;
- the previous remediation plan is referenced;
- the existing review boundary is recorded before execution;
- the drifted components from the plan are carried into execution;
- preflight gates passed before remediation steps;
- postcheck gates passed after remediation steps;
- rollback context stayed attached and was not needed;
- validation and sanitized evidence were refreshed after execution;
- public evidence records no public apply and no production apply;
- public evidence excludes addresses, credentials, raw logs, request bodies,
  private paths, and production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_private_infra_remediation_execution",
  "execution_model": "reviewed_private_control_plane_remediation_execution",
  "checks": {
    "operator_review_recorded": true,
    "reviewed_execution_recorded": true,
    "post_remediation_validation_recorded": true,
    "rollback_available_not_used": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public execution evidence uses only sanitized summaries. It does not
include live endpoints, server-specific paths, hostnames, network addresses,
credentials, raw logs, request bodies, private runtime connection values, or
production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/private-infra-remediation-execution.sanitized.json
```

The public-safe execution contract is stored at:

```text
infra/state-remediation/private-infra-remediation-execution.sanitized.json
```

## Why This Matters

Planning remediation is useful, but operations maturity shows up when the plan
is executed through review, preflight checks, postchecks, rollback context, and
fresh evidence. This layer demonstrates that DriveDesk can move from detection
to controlled operational response without exposing private infrastructure.
