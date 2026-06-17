# ADR-0018: Tenant Scope Query Helpers

Status: accepted

## Context

ADR-0017 made bearer-token sessions tenant-scoped. The next risk is duplicated
query filtering. If every endpoint manually implements tenant filtering, future
entities such as contracts, payments, lessons, documents, and tasks can drift.

## Decision

Centralize reusable tenant-scope helpers in:

```text
apps/api/drivedesk_api/tenant_scope.py
```

The first helpers cover existing Core resources:

- `actor_member_tenant_ids()`;
- `list_tenants_for_actor()`;
- `list_users_for_actor()`.

Handlers still perform explicit permission checks, but they delegate scoped list
queries to the tenant-scope module.

## Consequences

- Tenant filtering becomes reusable for new endpoint groups.
- Route handlers stay thinner.
- Tests can target tenant-scope behavior directly and through HTTP.
- Future repositories can reuse one pattern instead of copying query filters.

## Next Work

- ADR-0019 adds tenant-owned repository helpers for models that carry
  `tenant_id`.
- Apply those helpers to contracts, payments, lessons, files, tasks, and
  documents when those models exist.
- Add database-level row isolation when the Core schema stabilizes.
