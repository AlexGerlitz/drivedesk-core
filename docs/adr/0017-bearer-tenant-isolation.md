# ADR-0017: Bearer Tenant Isolation

Status: accepted

## Context

DriveDesk Core now has bearer-token auth, memberships, RBAC, and tenant-aware
permission checks. The remaining risk is role scope confusion:

```text
owner in one tenant != owner of the platform
```

If the highest tenant role is treated as a global role, a tenant owner can
accidentally gain platform-wide capabilities.

## Decision

Bearer-token requests must stay tenant-scoped:

- `GET /tenants` returns only tenants where the current user has active
  membership;
- `GET /users` returns only users who share one of the current user's tenants;
- tenant endpoints require membership in the requested tenant;
- global bootstrap endpoints reject bearer-token requests:
  - `POST /tenants`;
  - `POST /users`.

Development actor headers remain available for local bootstrap and controlled
seed flows. They are not product-session authorization.

## Consequences

- Tenant owners cannot create platform tenants through bearer-token sessions.
- Tenant owners cannot create platform users through bearer-token sessions.
- A valid token for tenant A cannot read tenant B data without membership in
  tenant B.
- Future product onboarding needs a dedicated tenant-scoped invitation flow or
  a dedicated platform-admin model.

## Next Work

- Add tenant-scoped repository helpers for future tenant-owned entities.
- Add a platform-admin model when real platform operations need it.
- Add database-level row isolation when the Core model is stable enough.
