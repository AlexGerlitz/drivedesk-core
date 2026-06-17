# DriveDesk Integration Connections

Integration connections are tenant-owned adapter profiles.

They answer:

```text
which configured external connection should this integration job use?
```

Before creating a connection, clients can call `GET /integration-adapters` to
discover which executable adapters support connection profiles and which mapping
shape they expect.

## API Shape

```text
GET /integration-adapters
POST /tenants/{tenant_id}/integration-connections
GET /tenants/{tenant_id}/integration-connections
```

Connection creation uses public-safe profile data:

```json
{
  "name": "Demo file import profile",
  "adapter_key": "file.import.fake",
  "status": "active",
  "config": {
    "mode": "synthetic"
  },
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  }
}
```

Secrets are not part of this contract. Provider credentials and webhook signing
material need a separate secret-store layer.

## File Import Usage

File import jobs can reference a connection:

```json
{
  "integration_connection_id": "connection-id",
  "source_name": "demo-leads-json",
  "source_format": "json",
  "records": []
}
```

The API verifies:

- the connection belongs to the same tenant;
- the connection is `active`;
- the connection uses the file-import adapter.

The created outbox event includes:

- `integration_connection_id`;
- selected `adapter_key`;
- safe mapping JSON;
- file import metadata and records.

## Audit Event

Connection creation writes:

```text
integration_connection.created
```

The audit event stores the connection id, adapter key, status, config keys, and
mapping keys. It does not store credentials.

## Metrics

`/metrics` exposes aggregate connection inventory:

```text
drivedesk_integration_connections{adapter_key="file.import.fake",status="active"} 1
```

Metric labels are intentionally limited to:

- `adapter_key`;
- `status`.

Connection names, connection ids, tenant ids, mapping values, config values,
credentials, and provider payloads must not appear in metrics.

## Why This Exists

This moves DriveDesk from a hardcoded adapter job to a configurable integration
hub:

```text
tenant -> integration connection -> integration job -> outbox -> worker -> adapter
```

Future adapters such as accounting export, website forms, bank imports,
telephony, or document providers can reuse the same connection shape.
