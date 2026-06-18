# DriveDesk Platform Admin Model

DriveDesk Core now separates tenant administration from platform
administration.

The core rule is:

```text
tenant owner != platform admin
```

A tenant owner can operate inside their own tenant. A platform admin can perform
global platform operations such as creating tenants, creating users, and reading
the platform-admin grant list. A platform admin can also revoke any auth
session through the control-plane session revocation endpoint.

## API Shape

```text
POST /platform/admins
GET /platform/admins
POST /tenants
POST /users
GET /tenants
GET /users
POST /auth/sessions/{session_id}/revoke
```

`POST /platform/admins` creates a platform-admin grant for an existing user.
The first grant can be created through the controlled bootstrap context. After a
user with that grant logs in, their bearer token can perform platform-level
operations.

`GET /auth/me` returns the current platform roles:

```json
{
  "platform_roles": ["platform_admin"]
}
```

## Verified Behavior

The Core API tests cover this flow:

```text
tenant owner logs in
tenant owner tries POST /platform/admins -> rejected
bootstrap context grants platform_admin to another user
platform admin logs in
GET /auth/me returns platform_roles=["platform_admin"]
platform admin creates a global tenant with bearer token -> allowed
platform admin creates a global user with bearer token -> allowed
platform admin reads /platform/admins -> allowed
platform admin revokes any tenant session -> allowed
```

This is the important SaaS boundary. A strong role inside one tenant does not
become a global platform role by accident.

## Data Model

Platform-admin grants are stored separately from tenant memberships:

```text
dd_platform_admins
  id
  user_id
  role
  status
  created_at
  updated_at
```

Tenant membership remains tenant-scoped:

```text
dd_memberships
  tenant_id
  user_id
  role
  status
```

That split keeps platform operations auditable and makes later hardening
straightforward.

## Audit And Outbox

Granting platform admin writes:

```text
platform_admin.granted
```

as both:

- a platform audit event;
- a platform outbox event.

This keeps global permission changes visible to operators and ready for future
notifications or approval workflows.

## Why This Matters

Multi-tenant platforms fail when local roles accidentally become global roles.
This model gives DriveDesk a clear platform boundary before adding more tenants,
admin UI, billing, or customer-facing controls.

DriveDesk is not only building CRUD endpoints. It is building the operational
control plane that a SaaS platform needs.

## Next Hardening

Recommended next slices:

1. Add approval workflow for platform-admin grants.
2. Add platform-admin metrics and public-safe audit examples.
3. Add database-level constraints after the Core model stabilizes.
