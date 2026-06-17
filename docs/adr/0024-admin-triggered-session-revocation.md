# ADR-0024: Admin-Triggered Session Revocation

## Status

Accepted

## Context

DriveDesk Core already exposes redacted auth session listing and a dedicated
platform-admin model. Operators can review active and revoked sessions, but they
also need a controlled way to terminate another user's session without database
access and without seeing raw bearer tokens or token hashes.

Session revocation must keep the tenant boundary from ADR-0017 and the
platform-admin boundary from ADR-0023.

## Decision

Add:

```text
POST /auth/sessions/{session_id}/revoke
```

The path value is the redacted session/token id already returned by
`GET /auth/sessions`. It is not a raw bearer token and it is not a token hash.

Access rules:

- platform admins can revoke any auth session;
- tenant owners/admins can revoke only sessions for users in tenants where they
  have `auth_session:write`;
- viewers and managers cannot revoke sessions;
- a tenant admin targeting a session outside their tenant scope receives
  `404 auth session not found` to avoid leaking session existence;
- development bootstrap actors can revoke sessions for local setup and
  verification.

Revocation writes a platform audit event:

```text
auth.token.admin_revoked
```

The audit actor is the admin performing the action. The target user/session is
stored as metadata.

## Consequences

- Operators can close risky or stale sessions through API controls.
- Raw bearer tokens and token hashes remain hidden.
- Tenant admins do not gain cross-tenant session control.
- Platform admins have a real control-plane session response path.
- Future UI can add a "revoke session" action on top of the same endpoint.
