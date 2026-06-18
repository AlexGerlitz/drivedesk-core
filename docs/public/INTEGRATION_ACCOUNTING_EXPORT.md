# Accounting Export Adapter

DriveDesk Core includes a public-safe mock accounting export adapter:
`accounting.export.mock`.

The adapter proves the outbound side of the Integration Hub. The same platform
path can later be used for real accounting, cash-register, bank, or ERP
providers without changing the core workflow model.

## Runtime Flow

```text
POST /tenants/{tenant_id}/integration-exports/accounting
  -> writes audit event
  -> enqueues accounting.export.requested
  -> worker executes accounting.export.mock
  -> result is stored on the outbox event
  -> retry/dead_letter jobs appear in operator review
```

The endpoint accepts a synthetic document batch:

```json
{
  "integration_connection_id": "optional-connection-id",
  "export_batch_id": "batch_2026_06",
  "documents": [
    {
      "document_id": "doc_001",
      "document_type": "invoice",
      "amount_cents": 120000,
      "currency": "RUB",
      "counterparty_ref": "counterparty_demo_1"
    }
  ]
}
```

The adapter validates each document summary and returns aggregate execution
results such as:

- `records_received`;
- `records_accepted`;
- `records_rejected`;
- `external_ref`;
- `details.accepted_document_ids`;
- `details.document_types`.

## Connection Scope

The adapter supports tenant-owned integration connections with the
`accounting:export` scope.

```json
{
  "name": "Demo accounting export profile",
  "adapter_key": "accounting.export.mock",
  "config": {
    "provider": "mock-accounting",
    "mode": "synthetic"
  },
  "scopes": ["accounting:export"]
}
```

If a disabled connection or a connection for another adapter is passed to the
export endpoint, the API rejects the request before enqueueing the outbox job.

## Failure Modes

The mock adapter can simulate two provider outcomes:

- `simulate_failure: "retryable"` moves the outbox event to `retry`;
- `simulate_failure: "permanent"` moves the outbox event to `dead_letter`.

Both states are visible through:

```text
GET /tenants/{tenant_id}/integration-operator-review
GET /tenants/{tenant_id}/integration-operator-review?adapter_key=accounting.export.mock
```

Operator review exposes only a safe summary:

```json
{
  "adapter_key": "accounting.export.mock",
  "operation_key": "accounting_export_execute",
  "required_connection_scope": "accounting:export",
  "payload_summary": {
    "payload_valid": true,
    "export_batch_id": "retryable-accounting-batch",
    "document_count": 1,
    "document_types": ["invoice"],
    "raw_documents_redacted": 1
  }
}
```

The raw `documents` payload is not returned by operator review.

## Public-Safe Boundary

This adapter is intentionally synthetic:

- no real provider credentials;
- no real accounting payloads;
- no personal data;
- no private business identifiers;
- no provider-specific protocol details.

The public repo can therefore show the architecture without exposing private
commercial integrations.
