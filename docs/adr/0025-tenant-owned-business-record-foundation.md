# ADR-0025: Tenant-Owned Business Record Foundation

Status: accepted

## Context

DriveDesk Core already has reusable tenant-owned query helpers, but they were
only exercised by platform primitives such as memberships, audit events, and
outbox events.

The next product direction needs contracts, payments, lessons, tasks, and
documents. Adding five separate domain models at once would create product
surface before the platform boundary is proven.

## Decision

Add a generic tenant-owned business record foundation:

```text
dd_business_records
```

The first supported `record_type` values are:

- `contract`;
- `payment`;
- `lesson`;
- `task`;
- `document`.

The API surface is:

```text
POST /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records?record_type=contract
```

Business record reads and writes use explicit RBAC permissions:

- `business_record:read`;
- `business_record:write`.

The list path uses `tenant_owned_select()` and `list_tenant_owned()` so new
business data follows the same tenant isolation boundary as existing Core
records.

Each created record writes:

- an audit event: `business_record.created`;
- an outbox event: `business_record.created`;
- adapter key: `internal.business_record`.

## Consequences

- DriveDesk gets a real tenant-owned business entity surface without committing
  too early to detailed contracts, payments, lessons, tasks, or document
  schemas.
- Future domain packs can split high-value record types into dedicated tables
  when their lifecycle becomes complex.
- Tenant isolation is proven against product-shaped data, not only Core admin
  tables.
- Public reviewers can see how platform primitives turn into business-facing
  API endpoints.
