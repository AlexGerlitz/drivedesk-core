# ADR-0026: Business Record Lifecycle And Metrics

Status: accepted

## Context

ADR-0025 introduced a tenant-owned business record foundation for contracts,
payments, lessons, tasks, and documents.

Creating records is not enough for a platform workflow. The system also needs a
small, auditable state transition path and aggregate operational visibility.

## Decision

Add a lifecycle transition endpoint:

```text
POST /tenants/{tenant_id}/business-records/{record_id}/transition
```

The transition updates the record `status` and writes:

- audit event: `business_record.status_changed`;
- outbox event: `business_record.status_changed`;
- adapter key: `internal.business_record`.

Add a storage-backed Prometheus metric:

```text
drivedesk_business_records{record_type="contract",status="approved"} 1
```

The metric uses only aggregate labels:

- `record_type`;
- `status`.

It must not expose titles, external references, payload data, user identifiers,
or tenant identifiers.

## Consequences

- Business records now behave like workflow objects, not only stored rows.
- Status changes are reviewable through audit and integration-ready through the
  outbox.
- Operators can inspect aggregate business state through `/metrics` without
  leaking sensitive business data.
- Future dedicated domain modules can reuse this lifecycle shape.
