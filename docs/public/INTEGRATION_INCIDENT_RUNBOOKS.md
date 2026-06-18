# Integration Incident Runbooks

Integration incident runbooks turn failed integration signals into operator
work.

DriveDesk already records outbox status, adapter retries, dead letters, and
provider reconciliation results. This layer creates tenant-owned incident cards
from those signals and attaches a public-safe runbook.

## Runbook Catalog

```text
GET /integration-runbooks
```

The catalog is public-safe and contains:

- runbook key;
- title;
- severity;
- source type;
- source statuses;
- alert name;
- recommended actions;
- expected evidence fields.

Current runbook keys:

| Runbook | Source | Status | Severity | Alert |
| --- | --- | --- | --- | --- |
| `integration.retry_backlog` | outbox event | `retry` | warning | `DriveDeskIntegrationRetries` |
| `integration.dead_letter` | outbox event | `dead_letter` | critical | `DriveDeskIntegrationDeadLetters` |
| `integration.reconciliation_mismatch` | reconciliation | `mismatched` | critical | `DriveDeskIntegrationReconciliationMismatch` |
| `integration.reconciliation_blocked` | reconciliation | `blocked` | critical | `DriveDeskIntegrationReconciliationBlocked` |
| `integration.reconciliation_pending` | reconciliation | `pending` | info | none |

## Incident Endpoints

```text
POST /tenants/{tenant_id}/integration-incidents
GET  /tenants/{tenant_id}/integration-incidents
POST /tenants/{tenant_id}/integration-incidents/{incident_id}/status
```

Create requires tenant write access. Listing requires tenant read access. Status
changes require tenant write access.

## Create Payload

```json
{
  "source_type": "reconciliation",
  "source_id": "reconciliation-id",
  "note": "operator checked provider dashboard"
}
```

Supported source types:

- `outbox_event`;
- `reconciliation`.

DriveDesk chooses the runbook from the source status:

- outbox `retry` -> `integration.retry_backlog`;
- outbox `dead_letter` -> `integration.dead_letter`;
- reconciliation `mismatched` -> `integration.reconciliation_mismatch`;
- reconciliation `blocked` -> `integration.reconciliation_blocked`;
- reconciliation `pending` -> `integration.reconciliation_pending`.

Processed outbox events and matched reconciliations do not create incidents.

## Response Shape

```json
{
  "id": "incident-id",
  "tenant_id": "tenant-id",
  "source_type": "reconciliation",
  "source_id": "reconciliation-id",
  "adapter_key": "accounting.export.mock",
  "operation_key": "accounting_export_execute",
  "runbook_key": "integration.reconciliation_mismatch",
  "severity": "critical",
  "status": "open",
  "summary": "Provider-side evidence does not match the result recorded by DriveDesk.",
  "recommended_action": "Review reconciliation diff keys and provider status.",
  "evidence_json": "{\"diff_keys\":[\"records_accepted\"]}",
  "created_at": "2026-06-18T00:00:00Z",
  "updated_at": "2026-06-18T00:00:00Z",
  "resolved_at": null
}
```

Incident statuses:

| Status | Meaning |
| --- | --- |
| `open` | New incident, no operator status change yet. |
| `acknowledged` | Operator has accepted ownership. |
| `resolved` | Operator marked the incident resolved. |

## Safe Evidence

Incident evidence intentionally stores safe operational facts:

- source type;
- source id;
- adapter key;
- operation key;
- outbox status;
- attempt count;
- whether an error exists;
- redacted document/record counts;
- reconciliation diff keys;
- provider status;
- whether a provider reference exists.

Incident evidence does not store:

- raw documents;
- raw import rows;
- names;
- phone numbers;
- payment metadata;
- provider response bodies;
- provider tokens;
- provider references;
- batch ids.

## Audit

Creating an incident writes:

```text
integration.incident.created
```

Changing status writes:

```text
integration.incident.status_changed
```

Audit metadata includes runbook key, source type, source id, adapter key,
severity, previous status, new status, and whether an operator note was present.

## Metrics

Prometheus exposes aggregate incident state:

```text
drivedesk_integration_incidents{adapter_key="accounting.export.mock",severity="critical",status="open"} 2
drivedesk_integration_incidents{adapter_key="accounting.export.mock",severity="warning",status="resolved"} 1
```

Metric labels avoid tenant ids, incident ids, source ids, provider references,
batch ids, document ids, names, phone numbers, and secrets.

## Operator Flow

```text
retry/dead_letter/mismatch signal
        |
        v
integration incident
        |
        v
runbook actions + audit trail + aggregate metrics
        |
        v
acknowledged -> resolved
```

This makes integration operations reviewable even when raw logs are unavailable
or unsafe to share.
