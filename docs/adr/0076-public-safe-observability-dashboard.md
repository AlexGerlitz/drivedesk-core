# ADR-0076: Public-Safe Observability Dashboard Contract

## Status

Accepted

## Context

DriveDesk Core already exposes public-safe metrics, logs, alert, and runbook
evidence. The public engineering surface also needs an operational dashboard
contract that shows how these signals become production support views without
publishing private Grafana dashboards or runtime telemetry.

## Decision

DriveDesk will expose a public-safe Observability Dashboard contract through:

- `docs/public/OBSERVABILITY_DASHBOARD.md`;
- `docs/public/evidence/observability-dashboard.sanitized.json`;
- `infra/observability/observability-dashboard.sanitized.json`;
- `GET /demo/observability-dashboard`;
- `GET /demo/public` under `observabilityDashboard`;
- `scripts/check_public_observability_dashboard.sh`.

The contract records dashboard groups, panel catalog entries, safe query shapes,
alert links, runbook links, and data boundaries.

## Consequences

- The public repository can prove dashboard design and alert linkage without
  exposing live telemetry.
- Dashboard examples stay tied to existing public-safe metrics, logs, alerts,
  and runbooks.
- Raw logs, request bodies, production screenshots, private addresses,
  credentials, and customer data remain outside the public export.
