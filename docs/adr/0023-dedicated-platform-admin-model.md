# ADR-0023: Dedicated Platform Admin Model

## Status

Accepted

## Context

DriveDesk Core already separates bearer-token tenant access from development
bootstrap headers. A tenant owner can manage tenant-scoped resources, but must
not automatically gain platform-wide capabilities.

Before this ADR, global tenant and user creation stayed behind bootstrap
context only. That proved the tenant boundary, but it did not provide a
product-shaped path for real platform operators.

## Decision

Add a dedicated `dd_platform_admins` grant model.

Platform-admin grants are separate from tenant memberships:

- tenant memberships live in `dd_memberships`;
- platform-admin grants live in `dd_platform_admins`;
- bearer auth resolves both membership roles and platform roles;
- `GET /auth/me` exposes active platform roles;
- `POST /platform/admins` creates a platform-admin grant;
- `GET /platform/admins` lists platform-admin grants;
- platform-admin bearer tokens can create global tenants and users;
- tenant owner bearer tokens remain rejected for platform bootstrap actions.

Granting platform admin writes `platform_admin.granted` to platform audit and
outbox streams.

## Consequences

- `owner in tenant A` remains different from `platform_admin`.
- Platform operations now have a bearer-token path instead of relying only on
  development headers.
- The first platform-admin grant still needs controlled bootstrap context.
- Future admin UI can manage platform operators through real API endpoints.
- ADR-0024 uses platform-admin grants for global session revocation without
  changing the tenant membership model.
- Future hardening can add approval flow and platform-admin metrics without
  changing the tenant membership model.
