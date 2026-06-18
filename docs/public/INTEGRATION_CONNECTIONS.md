# DriveDesk Integration Connections

Integration connections are tenant-owned adapter profiles.

They answer:

```text
which configured external connection should this integration job use?
```

Before creating a connection, clients can call `GET /integration-adapters` to
discover which executable adapters support connection profiles and which mapping
shape they expect.

Connection creation validates the submitted mapping against the selected adapter
descriptor. For `file.import.fake`, the required mapping keys are:

```text
external_id
display_name
```

Adapters that do not support tenant-owned connection profiles, such as
`internal.noop`, are rejected by the connection API.

Connection creation also validates requested scopes against the adapter
descriptor. Scope behavior is documented in `INTEGRATION_CONNECTION_SCOPES.md`.

## API Shape

```text
GET /integration-adapters
POST /tenants/{tenant_id}/integration-connections
GET /tenants/{tenant_id}/integration-connections
POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks
GET /tenants/{tenant_id}/integration-connections/{connection_id}/health
POST /tenants/{tenant_id}/integration-mapping-preview
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
  },
  "scopes": ["file_import:preview", "file_import:execute"]
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
- the connection uses the file-import adapter;
- the stored mapping still satisfies the runtime adapter descriptor.
- the connection has the `file_import:execute` scope.

The created outbox event includes:

- `integration_connection_id`;
- selected `adapter_key`;
- safe mapping JSON;
- file import metadata and records.

The worker applies the stored mapping before executing the file-import adapter.
For example, a connection can map `lead_id` to `external_id` and `full_name` to
`display_name`.

Before scheduling a job, clients can call
`POST /tenants/{tenant_id}/integration-mapping-preview` to see accepted and
rejected normalized rows without creating outbox work. When preview references a
stored connection, the connection must have the `file_import:preview` scope.

## Diagnostics

Connection profiles can be checked before scheduling integration work:

```text
POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks
GET /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks
GET /tenants/{tenant_id}/integration-connections/{connection_id}/health
```

Diagnostics store safe results in `dd_integration_connection_checks` and expose
latest status, last success, last failure, and check history. Details return
config key names, mapping key names, scopes, operation keys, and missing
operation scopes, but not config values, mapping values, credentials, raw
records, or raw documents. See `INTEGRATION_CONNECTION_DIAGNOSTICS.md`.

## Audit Event

Connection creation writes:

```text
integration_connection.created
integration_connection.health_checked
```

The audit event stores the connection id, adapter key, status, config keys, and
mapping keys. It also stores scope labels. It does not store credentials.

## Metrics

`/metrics` exposes aggregate connection inventory:

```text
drivedesk_integration_connections{adapter_key="file.import.fake",status="active"} 1
drivedesk_integration_connection_checks{adapter_key="file.import.fake",status="passed"} 1
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
