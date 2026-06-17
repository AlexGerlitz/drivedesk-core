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

## Why This Matters

Structured operation contracts keep the Integration Hub explicit:

- UI can show exactly which operations a profile can perform;
- SDK examples can point to the right endpoint and required scope;
- worker behavior can be documented per operation;
- public docs can describe 1C, bank, KKT, webhook, and file-import adapters
  through the same shape later.

This avoids building future integrations as one-off code paths.
