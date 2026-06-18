# DriveDesk Auth Observability

This document describes the public-safe auth observability contract. It avoids
private infrastructure details and real user data.

## Metrics

DriveDesk exposes aggregate auth metrics:

```text
drivedesk_auth_sessions{status="active"} 2
drivedesk_auth_sessions{status="revoked"} 1
drivedesk_auth_attempts_total{outcome="failure"} 3
drivedesk_metrics_storage_available 1
```

Safe labels:

- `status`;
- `outcome`.

Forbidden in auth metrics:

- email;
- user id;
- tenant id;
- token id;
- token hash;
- bearer token;
- request body.

## Alerts

The private staging alerting contract uses these Prometheus alert names:

| Alert | Meaning |
| --- | --- |
| `DriveDeskMetricsStorageUnavailable` | `/metrics` is scrapeable, but storage-backed aggregates are degraded. |
| `DriveDeskAuthFailureSpike` | Failed login attempts increased during the evaluation window. |
| `DriveDeskAuthLockedAttempts` | The failed-attempt guard blocked at least one login attempt. |

## Runbook Shape

The private runbook follows this order:

1. Check `/health`, `/ready`, and `/metrics`.
2. Check aggregate auth metrics in Prometheus.
3. Check API logs for safe event names.
4. Decide whether the activity is expected test traffic or suspicious behavior.
5. Re-run health and evidence workflows after the fix.

## Engineering Summary

This is the difference between "we have auth" and "we can operate auth."
DriveDesk treats login failures, lockouts, and degraded metrics as observable
incidents while keeping sensitive auth data out of public artifacts.
