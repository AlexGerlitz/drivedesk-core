# ADR-0022: Auth Security Alerts and Runbook

Status: accepted

## Context

ADR-0021 added public-safe aggregate auth metrics:

- `drivedesk_auth_sessions`;
- `drivedesk_auth_attempts_total`;
- `drivedesk_metrics_storage_available`.

Metrics alone are not enough for a DevOps-grade system. Operators also need
Prometheus alert rules, SLO mapping, and a runbook that explains what to check
without leaking auth-sensitive data.

## Decision

Add staging Prometheus alerts:

- `DriveDeskMetricsStorageUnavailable`;
- `DriveDeskAuthFailureSpike`;
- `DriveDeskAuthLockedAttempts`.

All three alerts route to:

```text
docs/runbooks/de-staging-auth-security.md
```

The alert expressions stay aggregate-only. They use metric labels such as
`status` and `outcome`, not users, tenants, emails, token ids, token hashes, raw
tokens, request bodies, or provider payloads.

Deploy, health, and evidence workflows must validate that the alert rules are
loaded. The evidence workflow also records whether auth metrics and
storage-backed metrics were present in the private staging scrape sample.

## Consequences

- Auth security now has the full SRE loop: metric, alert, runbook, and evidence.
- Public docs can describe the alerting contract without exposing private
  staging hostnames, addresses, credentials, or raw logs.
- Future production alert routing can reuse the same signal names while changing
  thresholds and receivers.
