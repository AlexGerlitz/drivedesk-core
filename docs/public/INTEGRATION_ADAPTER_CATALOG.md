# DriveDesk Integration Adapter Catalog

DriveDesk exposes a public-safe adapter catalog:

```text
GET /integration-adapters
```

The catalog answers:

```text
which adapters can this DriveDesk runtime execute, and what contract do they expect?
```

## Why It Exists

Connection profiles let a tenant configure an adapter. The adapter catalog lets
the admin UI, generated clients, smoke tests, and public API discover the
adapter contract before creating a connection or enqueueing a job.

This removes hardcoded UI assumptions such as:

```text
file.import.fake is probably a file-import adapter
```

and replaces them with runtime metadata:

```json
{
  "key": "accounting.export.mock",
  "name": "Mock Accounting Export",
  "status": "active",
  "direction": "outbound",
  "connection_profile_supported": true,
  "connection_profile_required": false,
  "required_mapping_keys": [],
  "supported_connection_scopes": ["accounting:export"],
  "default_connection_scopes": ["accounting:export"],
  "operation_contracts": [
    {
      "key": "accounting_export_execute",
      "event_type": "accounting.export.requested",
      "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
      "required_connection_scope": "accounting:export"
    }
  ],
  "capabilities": [
    "outbound export boundary",
    "connection scope enforcement",
    "retryable failure simulation"
  ]
}
```

## Catalog Fields

Each adapter descriptor includes:

| Field | Meaning |
| --- | --- |
| `key` | Stable adapter identifier used by outbox jobs and connection profiles. |
| `name` | Human-readable adapter name. |
| `status` | Runtime status such as `active`. |
| `category` | Adapter family, for example `file_import` or `internal`. |
| `direction` | Data direction, for example `inbound`, `outbound`, or `internal`. |
| `purpose` | Short public-safe explanation. |
| `connection_profile_supported` | Whether tenant-owned connection profiles can point at this adapter. |
| `connection_profile_required` | Whether a job must provide a connection profile. |
| `payload_schema` | Public-safe payload shape expected by the adapter. |
| `config_example` | Safe example config shape. |
| `mapping_example` | Safe example field mapping. |
| `required_mapping_keys` | Mapping keys that must be present when a tenant connection profile is created. |
| `supported_connection_scopes` | Operations a tenant-owned profile may request for this adapter. |
| `default_connection_scopes` | Scopes stored when a profile does not request explicit scopes. |
| `operation_contracts` | Machine-readable operations, endpoints, events, required scopes, idempotency keys, and recovery behavior. |
| `capabilities` | What the adapter proves. |
| `failure_modes` | Public-safe failure modes used for retry/dead-letter tests. |

## Current Runtime Adapters

The current catalog contains executable adapters only:

| Adapter | Direction | Connection Profile | Purpose |
| --- | --- | --- | --- |
| `file.import.fake` | `inbound` | supported | Synthetic file import adapter for contract tests and public demos. |
| `crm.bitrix24.mock` | `inbound` | supported | Synthetic CRM deal intake adapter for Bitrix24-style provider contracts. |
| `accounting.export.mock` | `outbound` | supported | Synthetic accounting export adapter for outbound contract tests. |
| `internal.noop` | `internal` | not supported | Internal acknowledgement path for default outbox events. |

Provider-specific real adapters can appear in private product work later. Public
runtime adapters appear in this catalog only when the worker/core can execute a
safe contract without real credentials or raw provider payloads.

## Relationship To Connection Profiles

The flow is:

```text
GET /integration-adapters
        |
        v
POST /tenants/{tenant_id}/integration-connections
        |
        v
POST /tenants/{tenant_id}/integration-mapping-preview
        |
        v
POST /tenants/{tenant_id}/business-provider-intake/preview
        |
        v
POST /tenants/{tenant_id}/integration-imports/file
        |
        v
POST /tenants/{tenant_id}/integration-exports/accounting
        |
        v
outbox -> worker -> adapter
```

The catalog is read-only. It does not store tenant data, connection names,
mapping values from real tenants, provider payloads, or sensitive provider
values.

## Adapter Operation Scenarios

The public demo includes `adapterScenarios` so the Integration Hub is visible as
an operational lifecycle, not only as a catalog.

| Scenario | Adapter | Operation | Phase | Scope | Evidence |
| --- | --- | --- | --- | --- | --- |
| File import mapping preview | `file.import.fake` | `file_import_preview` | `preview` | `file_import:preview` | `integration.mapping_preview.completed` |
| File import execution | `file.import.fake` | `file_import_execute` | `execute` | `file_import:execute` | `integration.file_import.requested` |
| CRM deal intake preview | `crm.bitrix24.mock` | `crm_deal_intake_preview` | `preview` | `crm:deal.preview` | `business_provider_intake.previewed` |
| CRM deal intake queue | `crm.bitrix24.mock` | `crm_deal_ingest_execute` | `execute` | `crm:deal.ingest` | `integration.crm_deal.ingest.requested` |
| Accounting export retry | `accounting.export.mock` | `accounting_export_execute` | `retry` | `accounting:export` | `integration.export.retry_scheduled` |
| Dead-letter operator review | `file.import.fake` | `file_import_execute` | `operator_review` | `file_import:execute` | `integration.operator_review.created` |

These scenarios make the adapter boundary reviewable through the same public
demo API, generated SDK, static fallback, and release gate.

## Public Verification

The public smoke test validates:

- `/integration-adapters` returns `file.import.fake`, `crm.bitrix24.mock`,
  `accounting.export.mock`, and `internal.noop`;
- OpenAPI includes `GET /integration-adapters`;
- the file-import descriptor exposes `connection_profile_supported`;
- the file-import descriptor exposes `required_mapping_keys`;
- the file-import descriptor exposes `supported_connection_scopes`;
- the file-import descriptor exposes `default_connection_scopes`;
- the file-import descriptor exposes `operation_contracts`;
- the file-import execute operation declares `integration.file_import.requested`;
- the accounting export operation declares `accounting.export.requested`;
- the accounting export operation declares `accounting:export`;
- the CRM adapter declares `crm_deal_intake_preview`,
  `crm_deal_ingest_execute`, `crm:deal.preview`, and `crm:deal.ingest`;
- the public demo exposes adapter scenarios for preview, execute, retry, and
  operator review;
- the file-import descriptor exposes mapping transform and preview capabilities;
- the file-import descriptor includes mapping and payload examples;
- the public demo adapter cards include connection-profile metadata.
