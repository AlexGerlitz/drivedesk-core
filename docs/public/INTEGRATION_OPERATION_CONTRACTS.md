# Integration Operation Contracts

DriveDesk adapters expose operation contracts in the runtime catalog.

An operation contract answers:

```text
what concrete operation can this adapter perform, how is it triggered, and what
scope/recovery behavior applies?
```

## Runtime Shape

`GET /integration-adapters` returns `operation_contracts`.

```json
{
  "key": "file_import_execute",
  "title": "Execute file import job",
  "trigger": "api.outbox.enqueue",
  "event_type": "integration.file_import.requested",
  "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
  "required_connection_scope": "file_import:execute",
  "idempotency_keys": ["tenant_id", "source_name", "source_format", "records_hash"],
  "retryable": true,
  "dead_letter": true,
  "operator_review": true
}
```

## File Import Operations

| Operation | Scope | Recovery |
| --- | --- | --- |
| `file_import_preview` | `file_import:preview` | no retry or dead-letter; read-only preview |
| `file_import_execute` | `file_import:execute` | retry, dead-letter, and operator review |

Preview is a read-only API operation. Execute is an outbox-backed operation that
the worker can process, retry, or move to dead-letter.

## CRM Deal Intake Operations

| Operation | Scope | Recovery |
| --- | --- | --- |
| `crm_deal_intake_preview` | `crm:deal.preview` | no retry or dead-letter; read-only provider intake preview |
| `crm_deal_ingest_execute` | `crm:deal.ingest` | retry, dead-letter, and operator review |

The CRM adapter uses a Bitrix24-style synthetic contract. Preview maps provider
facts into the `business-provider-intake/preview` boundary. Ingest queues safe
normalized deal facts through the outbox and keeps raw provider payloads,
credentials, names, phone numbers, emails, addresses, and tokens out of the
public response.

The adapter descriptor also exposes an `auth_profile`. That profile is separate
from operation scope: scopes say what the connection may do, while the auth
profile says where provider credentials and token exchange must live. For the
Bitrix24-style adapter the public demo requires no secret, but a real provider
connector must use server-side secret storage, private token exchange, and no
browser token storage.

## Accounting Export Operations

| Operation | Scope | Recovery |
| --- | --- | --- |
| `accounting_export_execute` | `accounting:export` | retry, dead-letter, and operator review |

The outbound export operation uses:

```json
{
  "key": "accounting_export_execute",
  "event_type": "accounting.export.requested",
  "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
  "required_connection_scope": "accounting:export",
  "idempotency_keys": ["tenant_id", "export_batch_id", "documents_hash"],
  "retryable": true,
  "dead_letter": true,
  "operator_review": true
}
```

This proves that inbound imports and outbound exports can use the same
operation-contract model.

## Scenario Coverage

`GET /demo/public` exposes adapter operation scenarios that map the contracts to
operator-visible behavior:

| Phase | Contract | Expected behavior |
| --- | --- | --- |
| `preview` | `file_import_preview` | Validate mapping and sample records without creating an outbox event. |
| `preview` | `crm_deal_intake_preview` | Normalize CRM deal facts into a safe provider intake preview. |
| `execute` | `file_import_execute` | Queue an idempotent outbox event and record audit evidence. |
| `execute` | `crm_deal_ingest_execute` | Queue CRM deal facts through the outbox with redaction evidence. |
| `retry` | `accounting_export_execute` | Keep a temporary provider failure retryable and visible. |
| `operator_review` | `file_import_execute` | Create a review card for dead-letter work with runbook context. |

The generated SDK validates these scenarios so clients can rely on the same
integration lifecycle shape.

## Why This Matters

Structured operation contracts keep the Integration Hub explicit:

- UI can show exactly which operations a profile can perform;
- UI can show the credential boundary without exposing credentials;
- SDK examples can point to the right endpoint and required scope;
- worker behavior can be documented per operation;
- public docs can describe 1C, bank, KKT, webhook, file-import, and accounting
  adapters through the same shape later.

This avoids building future integrations as one-off code paths.
