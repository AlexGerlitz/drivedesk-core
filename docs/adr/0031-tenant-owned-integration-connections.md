# ADR-0031: Tenant-Owned Integration Connections

## Status

Accepted

## Context

DriveDesk already has an adapter execution contract and a fake file import
adapter. That proves the worker and outbox path, but the adapter is still
selected directly by the endpoint.

A platform-grade integration hub needs tenant-owned connection profiles:

- one tenant can have multiple external connections;
- a job can reference a configured connection instead of hardcoding the adapter;
- connection mapping can be reviewed and audited;
- metrics can show connection inventory without exposing tenant data.

Secrets are intentionally out of scope for this slice. Connection profiles store
public-safe config and mapping only. Provider tokens and credentials need a
separate secret-store layer later.

## Decision

Add `dd_integration_connections`.

Each connection stores:

- tenant id;
- display name;
- adapter key;
- lifecycle status;
- config JSON;
- mapping JSON;
- created and updated timestamps.

Expose:

```text
POST /tenants/{tenant_id}/integration-connections
GET /tenants/{tenant_id}/integration-connections
```

Creating a connection validates that the adapter key is available in the current
runtime adapter registry.

File import jobs can optionally reference:

```json
{
  "integration_connection_id": "..."
}
```

When a connection is provided, the file import endpoint verifies that:

- the connection belongs to the same tenant;
- the connection is active;
- the connection uses `file.import.fake`.

The created outbox event stores the connection id and mapping in the adapter
payload.

## Observability

Expose aggregate connection inventory through:

```text
drivedesk_integration_connections{adapter_key="file.import.fake",status="active"} 1
```

Metric labels are limited to `adapter_key` and `status`.

## Consequences

- DriveDesk now has a real tenant-owned integration profile layer.
- Import jobs can be tied to explicit connection configuration.
- Connection creation is audit-visible through `integration_connection.created`.
- Public portfolio reviewers can see the adapter hub moving from hardcoded
  jobs toward configurable integration profiles.
- Secret management remains a separate future concern instead of being mixed
  into connection JSON.
