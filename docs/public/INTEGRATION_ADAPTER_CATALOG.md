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
  "auth_profile": {
    "mode": "mock_outbound_boundary",
    "public_demo_requires_secret": false,
    "real_provider_requires_secret": true,
    "secret_refs": ["ACCOUNTING_PROVIDER_API_KEY", "ACCOUNTING_PROVIDER_ENDPOINT"],
    "credential_placement": "server_secret_store",
    "token_exchange": "private_connector_only",
    "external_token_exchange": false,
    "data_boundaries": ["no_public_secrets", "server_side_provider_calls_only"]
  },
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
| `auth_profile` | Public-safe credential boundary: auth mode, whether public demo or real provider needs secrets, secret reference names, token exchange placement, and data-boundary rules. |
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

## Auth Profile Boundary

`auth_profile` is not a credential. It is the contract that says where
credentials would live when the mock adapter becomes a real provider adapter.

For example, `crm.bitrix24.mock` declares:

```json
{
  "mode": "oauth2_or_webhook_boundary",
  "public_demo_requires_secret": false,
  "real_provider_requires_secret": true,
  "secret_refs": ["BITRIX24_WEBHOOK_URL", "BITRIX24_CLIENT_SECRET"],
  "credential_placement": "server_secret_store",
  "token_exchange": "private_connector_only",
  "external_token_exchange": false,
  "data_boundaries": [
    "no_public_secrets",
    "no_browser_token_storage",
    "server_side_provider_calls_only"
  ]
}
```

This keeps the public demo usable with no secrets while still showing how a
real Bitrix24, bank, 1C, KKT, webhook, or accounting connector will be wired:
tokens stay server-side, browser code receives no provider tokens, and external
provider calls remain behind private connector code.

The end-to-end connector path is documented in
`PROVIDER_CONNECTOR_GUIDE.md`: provider class -> auth profile -> tenant-owned
connection profile -> mapping preview -> provider intake or export operation ->
outbox execution -> diagnostics, reconciliation, incidents, and operator
review.

The connector certification path is documented in
`CONNECTOR_CERTIFICATION.md`: provider profile -> capability manifest ->
contract fixtures -> local certification gate -> runtime readiness review ->
release proof. That path keeps future CRM, bank, accounting, ERP, KKT, webhook,
file, email, telephony, and custom API connectors aligned before private
provider code is added.

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
- the CRM adapter declares an `auth_profile` with
  `oauth2_or_webhook_boundary`, `server_secret_store`, and
  `no_browser_token_storage`;
- the public demo exposes adapter scenarios for preview, execute, retry, and
  operator review;
- the file-import descriptor exposes mapping transform and preview capabilities;
- the file-import descriptor includes mapping and payload examples;
- the public demo adapter cards include connection-profile metadata.
