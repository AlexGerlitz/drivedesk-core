# DriveDesk Business Records

DriveDesk Core now includes a small tenant-owned business record foundation.
It is intentionally generic: the goal is to prove the platform boundary before
building detailed product modules.

## API Shape

```text
POST /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records?record_type=contract
```

Supported public-safe record types:

- `contract`;
- `payment`;
- `lesson`;
- `task`;
- `document`.

## Why This Exists

The long-term platform needs contracts, payments, lessons, tasks, and
documents. Instead of adding five unfinished CRUD modules, this layer proves the
shared platform behavior once:

- tenant ownership through `tenant_id`;
- bearer-token tenant membership checks;
- explicit read/write permissions;
- audit events;
- outbox events;
- reusable tenant-owned repository helpers.

## Verified Behavior

The Core API tests cover:

- a manager creating `contract` and `payment` records inside their tenant;
- listing all records for a tenant;
- filtering records by `record_type`;
- rejecting cross-tenant reads;
- rejecting viewer writes;
- writing `business_record.created` audit events;
- enqueuing `business_record.created` outbox events with
  `adapter_key=internal.business_record`.

## Boundary

This is not a final domain model for contracts, payments, lessons, tasks, or
documents. It is the first stable platform path for tenant-owned business data.

Future domain modules can move a record type into a dedicated table when it
needs its own lifecycle, validation rules, integrations, or reporting shape.
