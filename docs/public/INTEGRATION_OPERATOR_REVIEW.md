# DriveDesk Integration Operator Review

Operator review is the read path for failed integration jobs.

It lets an operator answer: what failed, which adapter operation failed, whether
the job is retryable or needs manual review, and which audited retry endpoint
should be used after the issue is checked.

## API Shape

```text
GET /tenants/{tenant_id}/integration-operator-review
GET /tenants/{tenant_id}/integration-operator-review?status=dead_letter
GET /tenants/{tenant_id}/integration-operator-review?adapter_key=file.import.fake
GET /tenants/{tenant_id}/integration-operator-review?adapter_key=accounting.export.mock
```

The endpoint returns only jobs in:

- `retry`;
- `dead_letter`.

It uses the same tenant boundary and `outbox:read` permission as outbox
inspection.

## Response Shape

```json
{
  "id": "outbox-event-id",
  "adapter_key": "file.import.fake",
  "operation_key": "file_import_execute",
  "event_type": "integration.file_import.requested",
  "status": "dead_letter",
  "severity": "operator_review",
  "attempts": 1,
  "last_error": "Fake provider rejected the import contract.",
  "required_connection_scope": "file_import:execute",
  "payload_summary": {
    "payload_valid": true,
    "has_integration_connection": true,
    "source_format": "json",
    "record_count": 1,
    "mapping_keys": ["display_name", "external_id"],
    "raw_records_redacted": 1
  },
  "recommended_action": "review mapping/provider contract, then requeue with an operator reason",
  "retry_endpoint": "/tenants/{tenant_id}/outbox-events/{event_id}/retry"
}
```

## Redaction Boundary

The review endpoint intentionally does not return raw import records,
`source_name`, provider credentials, config values, or mapping values. It only
returns safe operational facts:

- adapter key;
- operation key;
- event type;
- lifecycle status;
- attempt count;
- last error;
- required connection scope;
- source format;
- record count;
- mapping key names;
- retry endpoint.

That keeps operator review useful without turning dashboards, screenshots, logs,
or public examples into data-leak surfaces.

For outbound accounting export jobs, the same endpoint returns a safe document
summary:

```json
{
  "adapter_key": "accounting.export.mock",
  "operation_key": "accounting_export_execute",
  "event_type": "accounting.export.requested",
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

The raw `documents` list is not returned.

## Operational Flow

```text
adapter failure -> retry/dead_letter -> operator review queue -> audited retry -> worker execution
```

Operator review does not mutate the job. Recovery still happens through:

```text
POST /tenants/{tenant_id}/outbox-events/{event_id}/retry
```

That retry request writes `outbox_event.retry_requested` to the audit log.

## Human Explanation

This is the difference between a background job system and an operable
integration platform. When a future 1C, bank, KKT, webhook, or file-import
adapter fails, DriveDesk can show a safe review card and a controlled retry path
instead of requiring direct database edits or raw log inspection.
