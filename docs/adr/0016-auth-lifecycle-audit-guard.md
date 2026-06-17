# ADR-0016: Auth Lifecycle Audit And Login Guard

Status: accepted

## Context

ADR-0015 added the first Core auth token foundation:

- credential verification;
- bearer access token issuing;
- current-user lookup;
- token-backed RBAC context.

That proves a real login path, but production-style auth also needs lifecycle
control and operational evidence.

## Decision

Add auth lifecycle hardening:

- `dd_auth_attempts` records login attempts by email, user id when known,
  outcome, reason, and creation time;
- repeated failed login attempts activate a configurable login guard;
- `POST /auth/logout` revokes the current bearer access token;
- auth events are written to platform audit with `tenant_id=platform`;
- auth audit event types include:
  - `auth.login.failed`;
  - `auth.login.locked`;
  - `auth.login.succeeded`;
  - `auth.token.revoked`.

The guard is configured through DriveDesk settings, not through policy files:

- `DRIVEDESK_AUTH_FAILED_LOGIN_LIMIT`;
- `DRIVEDESK_AUTH_FAILED_LOGIN_WINDOW_SECONDS`;
- `DRIVEDESK_AUTH_TOKEN_TTL_SECONDS`.

## Consequences

- A token can be invalidated before its natural expiry.
- Failed auth activity is visible in a dedicated table.
- Auth lifecycle activity is visible in the existing audit model.
- Security operations can be tested with ordinary API tests.
- UI can show auth sessions, failed attempts, and revoked sessions.

## Next Work

- Tenant-scoped query filters for every tenant-owned object.
- ADR-0020 adds admin-visible auth session listing.
- ADR-0021 adds aggregate auth observability metrics.
- External identity provider or refresh-session design.
