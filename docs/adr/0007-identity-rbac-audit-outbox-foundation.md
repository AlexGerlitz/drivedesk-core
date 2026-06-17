# ADR-0007: Identity, RBAC, Audit, and Outbox Foundation

Status: accepted

## Context

After Sprint 0, DriveDesk Core had a clean API, worker, Docker Compose runtime,
and migration skeleton. The next layer needs real platform behavior before any
deployment or Kubernetes work is useful.

## Decision

Implement Sprint 1 as a minimal Core platform slice:

- `dd_users`;
- `dd_memberships`;
- `dd_outbox_events`;
- tenant CRUD foundation;
- user CRUD foundation;
- membership creation and listing;
- RBAC permissions for owner, admin, manager, and viewer;
- audit records for important writes;
- outbox events for important writes;
- worker processing for pending outbox rows.

For now, actor context is supplied through development headers:

- `X-Actor-Id`;
- `X-Actor-Role`.

This is intentionally not the final authentication system. It exists so Core
permissions, audit, and endpoint behavior can be built and tested before auth
provider decisions are made. Requests without an explicit role use `viewer`
permissions.

## Consequences

- DriveDesk Core can represent organizations and users.
- Tenant-scoped roles are now part of the data model.
- Write operations have a visible audit trail.
- Integrations and notifications have a future delivery path through outbox.
- The worker has a real processing responsibility.
- A real auth layer is still required before production use.
