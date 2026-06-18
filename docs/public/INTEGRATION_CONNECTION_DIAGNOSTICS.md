# Integration Connection Diagnostics

DriveDesk Core includes a public-safe diagnostics path for tenant-owned
integration connections.

The diagnostics path answers:

```text
is this connection profile structurally usable, which operations can it run,
and what was the latest safe health result?
```

## API Shape

```text
POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks
GET /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks
GET /tenants/{tenant_id}/integration-connections/{connection_id}/health
```

The `POST` endpoint runs a synthetic preflight check and stores the result in
`dd_integration_connection_checks`.

The check validates:

- tenant ownership;
- connection status;
- adapter existence;
- adapter connection-profile support;
- mapping key requirements;
- mapping value shape;
- supported connection scopes;
- executable operation keys for the selected scopes.

## Safe Result Shape

Example health-check result:

```json
{
  "adapter_key": "file.import.fake",
  "status": "passed",
  "summary": "Integration connection diagnostics passed.",
  "details_json": {
    "adapter_key": "file.import.fake",
    "connection_status": "active",
    "mapping_keys": ["display_name", "external_id"],
    "config_keys": ["mode"],
    "scopes": ["file_import:preview"],
    "operation_keys": ["file_import_preview", "file_import_execute"],
    "executable_operation_keys": ["file_import_preview"],
    "missing_operation_scopes": ["file_import:execute"]
  }
}
```

The details include key names and operation metadata only. They do not include
raw config values, mapping values, provider credentials, tenant-specific
payloads, imported records, exported documents, or connection names.

## Health Summary

The summary endpoint returns the latest lifecycle signal for a connection:

```json
{
  "latest_status": "failed",
  "latest_checked_at": "2026-06-18T10:00:00Z",
  "last_success_at": "2026-06-18T09:55:00Z",
  "last_failure_at": "2026-06-18T10:00:00Z",
  "check_count": 2,
  "latest_summary": "synthetic provider is unavailable"
}
```

This gives the admin UI a simple card:

```text
last check failed, previous success existed, operator should inspect provider availability
```

## Metrics

The API metrics endpoint exposes aggregate diagnostics:

```text
drivedesk_integration_connection_checks{adapter_key="file.import.fake",status="passed"} 1
drivedesk_integration_connection_checks{adapter_key="file.import.fake",status="failed"} 1
drivedesk_integration_connection_check_duration_milliseconds{adapter_key="file.import.fake",status="passed"} 2.4
```

Labels are limited to:

- `adapter_key`;
- `status`.

No tenant ids, connection ids, connection names, config values, mapping values,
credentials, request bodies, raw records, or raw documents are exported as
metric labels.

## Audit

Every health-check run writes:

```text
integration_connection.health_checked
```

The audit event stores safe metadata such as adapter key, check status,
duration, detail key names, and whether the failure was simulated.

## Human Explanation

This turns integrations into an operable platform surface. An operator can test
a connection before running imports or exports, see a safe history of checks,
and use metrics for dashboards and alerts without exposing private provider
details.
