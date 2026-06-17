# ADR-0015: Core Auth Token Foundation

Status: accepted

## Context

DriveDesk Core already has tenants, users, memberships, RBAC, audit, and outbox
events. Until this decision, endpoint authorization was tested through
development actor headers:

- `X-Actor-Id`;
- `X-Actor-Role`.

That was useful for building permission checks early, but it did not represent
real product authentication.

## Decision

Add a small first-party auth foundation:

- `dd_users.credential_hash` stores a derived credential hash;
- `dd_access_tokens` stores access token hashes and token lifecycle state;
- `POST /auth/login` verifies the user credential and returns a bearer token;
- `GET /auth/me` returns the current user and active memberships;
- bearer tokens resolve into the same `ActorContext` used by RBAC;
- tenant endpoints use the membership role for the requested tenant.

The actual bearer token is returned to the client once. The database stores only
the token hash.

Development actor headers remain available for bootstrap and local setup. They
should not be treated as the product auth path.

## Consequences

- DriveDesk now has a real login/session foundation for API clients.
- RBAC is no longer only a header-driven test mechanism.
- Tenant endpoint access can be denied when a valid token has no tenant
  membership.
- The current approach keeps the project dependency-light while the platform
  surface is still moving.
- Later hardening should add token revocation, auth audit events, login attempt
  rate limiting, refresh sessions or an external identity provider, and deeper
  tenant-scoped query filters.
