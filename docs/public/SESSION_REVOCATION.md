# DriveDesk Session Revocation

DriveDesk Core now supports admin-triggered auth session revocation.

This turns auth session review into an operational control:

```text
review session -> decide risk -> revoke session -> audit event
```

## API Shape

```text
GET /auth/sessions
POST /auth/sessions/{session_id}/revoke
```

`GET /auth/sessions` returns redacted session rows. It does not expose raw
bearer tokens or token hashes.

`POST /auth/sessions/{session_id}/revoke` closes one visible session by its
redacted session id.

## Access Rules

The endpoint keeps tenant and platform control separate:

- platform admins can revoke any auth session;
- tenant owners/admins can revoke only sessions for users inside tenants where
  they have `auth_session:write`;
- viewers and managers cannot revoke sessions;
- cross-tenant revoke attempts return `404 auth session not found`;
- raw bearer tokens and token hashes are never required.

## Verified Behavior

The Core API tests cover:

```text
tenant viewer lists sessions -> rejected
tenant viewer revokes session -> rejected
tenant owner revokes visible tenant session -> allowed
tenant owner revokes known session id outside tenant -> 404
platform admin revokes any tenant session -> allowed
revoked bearer token cannot call /auth/me anymore
```

## Audit Event

Admin-triggered revocation writes:

```text
auth.token.admin_revoked
```

as a platform audit event.

The actor is the admin performing the action. The target user/session is stored
as metadata, so operators can answer:

```text
who revoked which session and when?
```

## Why This Matters

Session revocation is a practical control-plane feature. It is what an operator
needs when:

- a staff member leaves;
- a device is lost;
- an account looks suspicious;
- a token should be closed without waiting for expiry.

For the public engineering surface, this proves DriveDesk is moving from
"auth exists" toward "auth is operable".
