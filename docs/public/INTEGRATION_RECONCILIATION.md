# Integration Reconciliation

Integration reconciliation records safe evidence that an external provider
accepted, partially accepted, rejected, or has not yet processed an integration
job.

It answers a production operator question:

```text
The outbox worker says the job finished. Does the provider-side evidence agree?
```

## Endpoints

```text
POST /tenants/{tenant_id}/integration-reconciliations
GET  /tenants/{tenant_id}/integration-reconciliations
```

The create endpoint requires tenant write access. The list endpoint requires
tenant read access.

## Create Payload

```json
{
  "outbox_event_id": "outbox-event-id",
  "provider_status": "partial_success",
  "provider_reference": "provider-batch-reference",
  "records_received": 3,
  "records_accepted": 2,
  "records_rejected": 1,
  "note": "operator checked provider dashboard"
}
```

The payload intentionally accepts only safe provider evidence:

- provider status;
- provider batch/reference id;
- aggregate record counts;
- optional note presence.

It does not accept raw documents, imported rows, names, phone numbers, payment
metadata, provider tokens, or provider response bodies.

## Result Shape

```json
{
  "id": "reconciliation-id",
  "tenant_id": "tenant-id",
  "outbox_event_id": "outbox-event-id",
  "adapter_key": "accounting.export.mock",
  "operation_key": "accounting_export_execute",
  "status": "matched",
  "summary": "Provider evidence matches outbox result evidence.",
  "expected_json": "{\"records_accepted\":2}",
  "actual_json": "{\"records_accepted\":2}",
  "diff_json": "{}",
  "created_at": "2026-06-18T00:00:00Z"
}
```

Statuses:

| Status | Meaning |
| --- | --- |
| `matched` | Provider evidence agrees with outbox result evidence. |
| `mismatched` | Provider evidence differs from outbox result evidence. |
| `pending` | The outbox job has not produced processed evidence yet. |
| `blocked` | The outbox job is dead-lettered and must be fixed before reconciliation can pass. |

## Safe Diff

For processed jobs, DriveDesk compares:

- adapter result status;
- external/provider reference;
- records received;
- records accepted;
- records rejected.

Example mismatch:

```json
{
  "records_accepted": {
    "expected": 2,
    "actual": 1
  },
  "records_rejected": {
    "expected": 1,
    "actual": 2
  }
}
```

The diff contains only aggregate values. Raw source rows and documents stay out
of reconciliation storage.

## Audit

Creating a reconciliation writes:

```text
integration.reconciliation.recorded
```

Audit metadata includes:

- reconciliation id;
- outbox event id;
- adapter key;
- operation key;
- reconciliation status;
- diff keys;
- provider status;
- whether a provider reference was present.

Audit metadata does not include raw provider payloads or provider secrets.

## Metrics

Prometheus exposes aggregate reconciliation state:

```text
drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="matched"} 1
drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="mismatched"} 1
```

Metric labels intentionally avoid:

- tenant ids;
- outbox event ids;
- provider references;
- record ids;
- document ids;
- names;
- phone numbers;
- secrets.

## Operator Flow

```text
API request -> outbox job -> worker execution -> provider evidence -> reconciliation
```

If reconciliation is `matched`, the operator has evidence that the external
provider agrees with DriveDesk's adapter result.

If reconciliation is `mismatched`, the operator can inspect the safe diff and
decide whether the provider dashboard, adapter mapping, or outbox job requires a
fix.

If reconciliation is `pending`, the job should finish before a final comparison.

If reconciliation is `blocked`, the outbox retry or operator-review path should
be handled first.
