# ADR-0021: Auth Observability Metrics

Status: accepted

## Context

DriveDesk Core now has credential auth, bearer access tokens, token revocation,
failed-attempt recording, a login guard, audit events, and redacted
tenant-scoped session listing.

Those features are useful only if operators can see auth health without opening
raw user data. The observability layer needs a small public-safe signal for:

- active vs revoked session state;
- successful, failed, and locked login attempts;
- future alert rules around suspicious auth behavior;
- demo and CI checks that prove auth state is observable without exposing
  emails, token hashes, bearer tokens, or tenant-specific identifiers.

## Decision

Expose aggregate-only auth metrics from `/metrics`:

- `drivedesk_auth_sessions{status="active|revoked"}` as a gauge;
- `drivedesk_auth_attempts_total{outcome="success|failure|locked"}` as a
  counter-style total derived from retained auth attempt rows.

The only auth metric labels are:

- `status`;
- `outcome`.

The metrics endpoint must not emit:

- user email;
- user id;
- tenant id;
- token id;
- token hash;
- bearer token;
- request body;
- provider payload.

The public demo smoke now checks that auth metric families exist and that common
secret or identifier field names are absent from the metrics output.

The metrics endpoint degrades instead of failing when storage-backed aggregate
queries are unavailable. In that case it returns the static process/readiness
families, empty storage-backed families, and:

```text
drivedesk_metrics_storage_available 0
```

## Consequences

- Auth is now visible in the same Prometheus surface as API, readiness, outbox,
  and integration health.
- Public reviewers can see that security-sensitive flows are observable without
  seeing private runtime data.
- The public demo and staging scrape path can keep returning Prometheus text
  even if storage-backed metrics are temporarily unavailable.
- ADR-0022 adds alert rules and a runbook on top of these aggregate signals.
- If auth attempt retention is introduced later, the metric name and type should
  be reviewed so it still matches the retention behavior.
