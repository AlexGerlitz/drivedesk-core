# DriveDesk Tenant Isolation

DriveDesk Core is a multi-tenant platform foundation. A user can have a role in
one tenant without becoming a platform-wide administrator.

## Current Rules

- Bearer-token requests are resolved through active memberships.
- `GET /tenants` returns only tenants where the current user has membership.
- `GET /users` returns only users who share one of the current user's tenants.
- Tenant endpoints require membership in the requested tenant.
- A valid bearer token is rejected when it targets a tenant outside the user's
  memberships.
- Global platform endpoints require a dedicated platform-admin grant:
  - `POST /platform/admins`;
  - `POST /tenants`;
  - `POST /users`.
- Tenant-owner bearer tokens are rejected for those platform operations.
- Platform-admin bearer tokens can list and create global tenant/user records.
- Tenant-owned business records require membership in the requested tenant.

Bootstrap headers still exist for local setup and the first controlled
platform-admin grant. They are not treated as tenant-owner capabilities.

## Why This Matters

Multi-tenant isolation is one of the highest-risk SaaS boundaries. The important
rule is simple:

```text
owner in tenant A != owner of the whole platform
```

This keeps role checks aligned with the requested tenant instead of only using
the highest role the user has anywhere.

## Verified Behavior

The Core API tests cover this scenario:

```text
tenant A owner logs in
tenant B exists
tenant A owner lists tenants -> only tenant A
tenant A owner lists users -> only tenant A users
tenant A owner reads tenant B -> rejected
tenant A owner reads tenant B memberships -> rejected
tenant A owner creates global tenant/user with bearer token -> rejected
tenant A owner grants platform admin -> rejected
platform admin creates global tenant/user with bearer token -> allowed
tenant A manager creates tenant A business record -> allowed
tenant A manager reads tenant B business records -> rejected
tenant B viewer writes tenant B business record -> rejected
```

## Platform Admin Boundary

Platform administration is stored separately from tenant membership:

```text
dd_platform_admins
```

That table grants `platform_admin` to a user without changing any tenant role.
Bearer auth resolves both tenant memberships and platform-admin grants, then
keeps the checks separate:

- tenant roles drive tenant-scoped access;
- platform-admin grants drive platform-scoped access;
- tenant owners cannot create global platform records by accident.

## Reusable Scope Module

Tenant filtering is centralized in:

```text
apps/api/drivedesk_api/tenant_scope.py
```

Current helpers:

- `actor_member_tenant_ids()`;
- `list_tenants_for_actor()`;
- `list_users_for_actor()`.

The goal is to keep future endpoint groups from copying tenant filters by hand.
When contracts, payments, lessons, documents, and tasks are added, they should
use the same tenant-scope pattern.

## Tenant-Owned Repository Helper

Tenant-owned query construction is centralized in:

```text
apps/api/drivedesk_api/tenant_repository.py
```

Current helpers:

- `tenant_owned_select()`;
- `list_tenant_owned()`.

Current tenant-owned list endpoints for memberships, audit events, outbox
events, and business records use the helper after explicit permission checks.
The point is to make `tenant_id` filtering the default path for future
contracts, payments, lessons, documents, and tasks.

## Business Record Boundary

The first product-shaped tenant-owned table is:

```text
dd_business_records
```

It supports `contract`, `payment`, `lesson`, `task`, and `document` record
types through one shared platform path. This proves tenant isolation before
those record types grow into dedicated domain modules.

## Request Flow

```mermaid
flowchart LR
  Token["Bearer Token"] --> Actor["Actor Context"]
  Actor --> Memberships["Active Memberships"]
  Actor --> PlatformGrant["Platform Admin Grant"]
  Memberships --> TenantCheck["Requested Tenant Check"]
  TenantCheck --> Allow["Allow Tenant Operation"]
  TenantCheck --> Reject["Reject Cross-Tenant Operation"]
  PlatformGrant --> PlatformOp["Platform Operation"]
  PlatformOp --> AllowPlatform["Allow"]
```

## Next Hardening

Recommended next slices:

1. Add public-safe tenant-isolation metrics with synthetic data.
2. Add database-level row isolation once the Core data model stabilizes.
3. Split high-value business record types into dedicated domain modules when
   their lifecycle requires it.
