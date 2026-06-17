# ADR-0019: Tenant-Owned Repository Helpers

Status: accepted

## Context

ADR-0018 centralized actor-level tenant scope for tenant and user list queries.
The next boundary is tenant-owned data. Existing resources such as memberships,
audit events, and outbox events all have `tenant_id`; future resources such as
contracts, payments, lessons, tasks, and documents will follow the same shape.

If each handler writes `where(model.tenant_id == tenant_id)` by hand, tenant
isolation becomes easy to copy incorrectly.

## Decision

Centralize tenant-owned query construction in:

```text
apps/api/drivedesk_api/tenant_repository.py
```

The first helpers are:

- `tenant_owned_select()`;
- `list_tenant_owned()`.

Current tenant-owned list endpoints for memberships, audit events, and outbox
events use this helper after explicit permission checks.

## Consequences

- New tenant-owned models have one default query pattern.
- Route handlers stay focused on HTTP validation and permission checks.
- Tests can prove the helper rejects non-tenant-owned models.
- Future repository/service modules can build on the helper instead of copying
  raw SQLAlchemy filters.

## Next Work

- Use this helper for new contract, payment, lesson, task, and document models.
- Add model-specific repository classes only when the query logic becomes more
  complex than simple tenant filtering.
- Add database-level row isolation after the Core schema stabilizes.
