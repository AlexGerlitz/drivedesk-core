# ADR-0020: Admin-Visible Auth Session Listing

Status: accepted

## Context

DriveDesk Core already has credential login, bearer access tokens, logout,
failed-attempt recording, and auth audit events. Operators still need a safe way
to see session state without exposing raw access tokens or token hashes.

Auth session visibility must also respect tenant boundaries. A tenant admin
should not gain platform-wide session visibility just because they are an admin
inside one tenant.

## Decision

Add:

```text
GET /auth/sessions
```

The endpoint returns redacted session rows:

- token id;
- user id;
- user email and display name;
- status;
- created, expires, last-used, and revoked timestamps;
- visible tenant ids.

It never returns raw access tokens or token hashes.

Bearer-token callers can see sessions only for users in tenants where their own
membership role has `auth_session:read`. Development bootstrap actors can list
all sessions for local setup and verification.

## Consequences

- Session state becomes reviewable through the API.
- Revoked tokens stay visible for operational review.
- Tenant admins get tenant-scoped visibility instead of global visibility.
- Future admin actions such as force-revoking another session can build on this
  endpoint and permission model.

## Next Work

- Add admin-triggered token revocation for tenant-scoped sessions.
- Add stronger device/session metadata when clients provide it.
- Add public-safe auth/session metrics with synthetic data.
