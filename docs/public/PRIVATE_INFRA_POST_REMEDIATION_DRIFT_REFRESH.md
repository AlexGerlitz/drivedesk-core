# Private Infrastructure Post-Remediation Drift Refresh

DriveDesk includes a public-safe post-remediation drift refresh evidence layer.
It records the read-only verification step after reviewed remediation execution,
while keeping public artifacts free of live endpoints, credentials, raw logs,
private paths, request bodies, and production data.

## Command

```bash
bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh
```

## What The Check Does

The check validates the closed operational loop:

```text
drift detected
    |
remediation plan reviewed
    |
private staging execution completed
    |
read-only drift refresh
    |
residual drift decision
    |
sanitized public evidence
```

The check verifies:

- the post-remediation refresh contract is present;
- the previous remediation execution is referenced;
- the original drifted components are carried forward;
- the refresh is read-only;
- desired and observed state sources are compared again;
- runtime, observability, and backup evidence are rechecked;
- previously drifted components are marked resolved;
- no residual or accepted drift remains in the sanitized snapshot;
- public evidence records no OpenTofu apply, no GitOps sync, no runtime
  mutation, no service restart, and no production apply;
- public evidence excludes addresses, credentials, raw logs, request bodies,
  private paths, and production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_private_infra_post_remediation_drift_refresh",
  "refresh_model": "post_remediation_private_infra_drift_refresh",
  "checks": {
    "remediation_execution_referenced": true,
    "resolved_components_recorded": true,
    "no_residual_drift_recorded": true,
    "read_only_refresh_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drift refresh evidence uses only sanitized summaries. It does not
include live endpoints, server-specific paths, hostnames, network addresses,
credentials, raw logs, request bodies, private runtime connection values, or
production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/private-infra-post-remediation-drift-refresh.sanitized.json
```

The public-safe refresh contract is stored at:

```text
infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json
```

## Why This Matters

Remediation is not complete when an action runs. It is complete when the system
is checked again and the remaining drift decision is recorded. This layer shows
that DriveDesk treats operations as a closed loop: detect, plan, execute,
verify, and keep scheduled validation running.
