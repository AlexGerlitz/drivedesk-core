# ADR-0038: Business Record Lifecycle Policy Catalog

Status: accepted

## Context

DriveDesk has tenant-owned business records for contracts, payments, lessons,
tasks, and documents. The first lifecycle endpoint can change a record status
and emits audit/outbox events, but the platform also needs a machine-readable
way to describe normal status paths before UI and workflow automation become
larger.

If lifecycle rules live only in frontend conditionals or scattered service code,
workflow rules, generated clients, and operators will drift from each other.

## Decision

Add a core lifecycle policy catalog in `packages/core` and expose it through:

```text
GET /business-record-lifecycle-policies
```

Add a tenant-scoped preview endpoint:

```text
POST /tenants/{tenant_id}/business-records/lifecycle-preview
```

The preview endpoint returns whether a proposed transition is valid, the allowed
next statuses, a human-readable reason, and whether the source status is
terminal. It does not mutate the record.

## Consequences

- UI can render valid next actions from API metadata.
- Workflow automation can reuse the same lifecycle vocabulary.
- The public OpenAPI schema documents domain behavior, not only CRUD paths.
- Future enforcement can reuse the same helper when invalid transitions should
  become hard API failures.
- No migration is required because this sprint adds metadata and preview logic,
  not a new persistence table.
