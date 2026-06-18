# Private Infrastructure Scheduled Alerting

DriveDesk includes public-safe alerting evidence for the recurring scheduled
validation loop. The goal is to show what happens when a scheduled validation
is missed or fails, without exposing private infrastructure, credentials, logs,
or production data.

## Command

```bash
bash scripts/check_public_private_infra_scheduled_alerting.sh
```

## What This Adds

Scheduled validation already proves that checks should run repeatedly. Scheduled
alerting adds the response path:

```text
scheduled validation signal
    |
missed run / failed run / secret boundary failure
    |
alert policy
    |
GitHub Actions failure artifact or operator review
    |
runbook-backed release hold
```

## Alert Signals

The public-safe alerting contract records three signals:

- `infra.scheduled_validation.missed` - the latest run is older than the
  expected interval;
- `infra.scheduled_validation.failed` - the workflow ran and failed;
- `infra.scheduled_validation.secret_boundary_failed` - the public/private
  secret boundary recheck failed.

## Workflow Failure Handler

The scheduled validation workflow includes a failure-only handler:

```text
Emit scheduled validation alert payload
Upload scheduled validation alert payload
```

The uploaded artifact is named:

```text
public-scheduled-validation-alert
```

It contains only a sanitized alert payload with event type, severity, runbook
key, notification route, and production-data boundary.

## Runbook Behavior

The runbook model is intentionally simple:

- missed run: manually dispatch the workflow and check GitHub Actions
  availability;
- failed run: inspect the failed job, run the checker locally, and keep
  promotion blocked;
- secret boundary failure: stop public export and inspect changed files before
  continuing.

## Redaction Boundary

The public scheduled alerting evidence does not include live endpoints,
hostnames, addresses, private paths, credentials, raw logs, request bodies,
runtime connection values, external notification credentials, or production
data.

## Why This Matters

A green scheduled check is useful, but a failed scheduled check must also have
a response path. This layer turns recurring validation into an operational
control: missed or failed checks become reviewable incidents instead of silent
background noise.
