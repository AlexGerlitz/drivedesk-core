# DriveDesk Integration Adapters

This document describes the public-safe adapter foundation in DriveDesk Core.
It uses synthetic data and fake providers only.

## Goal

DriveDesk should be the operational workspace. External systems should connect
through adapters instead of leaking provider-specific payloads into the core
domain.

The first implementation slice is a fake file import adapter. It proves the
shape needed for later providers:

- provider-neutral adapter contract;
- API-created integration job;
- outbox event;
- worker execution;
- retry state for temporary failures;
- dead-letter state for permanent failures;
- result payload stored on the outbox event;
- public demo and OpenAPI evidence.

## Current Adapter Contract

Adapter execution returns a normalized result:

```json
{
  "adapter_key": "file.import.fake",
  "status": "partial_success",
  "message": "Imported 2 fake records from demo-leads-json.",
  "records_received": 3,
  "records_accepted": 2,
  "records_rejected": 1,
  "external_ref": "fake-import:demo-leads-json"
}
```

Temporary failures become retryable worker state. Permanent failures become
dead-letter state and need operator review.
Reviewed `retry` and `dead_letter` events can be moved back to `pending`
through the outbox recovery endpoint. See `OUTBOX_RECOVERY.md`.

## API Slice

The public OpenAPI schema includes:

```text
GET /integration-adapters
POST /tenants/{tenant_id}/integration-connections
GET /tenants/{tenant_id}/integration-connections
POST /tenants/{tenant_id}/integration-imports/file
POST /tenants/{tenant_id}/outbox-events/{event_id}/retry
```

`GET /integration-adapters` returns the executable runtime adapter catalog with
public-safe metadata, payload shape, mapping examples, and connection-profile
support flags. See `INTEGRATION_ADAPTER_CATALOG.md`.

The file-import endpoint accepts synthetic file-import records and creates an outbox event
with `adapter_key = file.import.fake`.
File imports can also reference a tenant-owned integration connection profile.
See `INTEGRATION_CONNECTIONS.md`.

## Worker Flow

```mermaid
sequenceDiagram
  participant API as API
  participant Outbox as Outbox
  participant Worker as Worker
  participant Adapter as File Import Adapter

  API->>Outbox: enqueue integration.file_import.requested
  Worker->>Outbox: fetch pending or due retry event
  Worker->>Adapter: execute normalized adapter payload
  Adapter-->>Worker: success, retryable failure, or permanent failure
  Worker->>Outbox: processed, retry, or dead_letter
```

## Status Model

| Status | Meaning |
| --- | --- |
| `pending` | Event is waiting for worker execution. |
| `processed` | Adapter completed and result was stored. |
| `retry` | Adapter failed temporarily and has `next_retry_at`. |
| `dead_letter` | Adapter failed permanently or exhausted retries. |

## Human Explanation

This is the first real proof of the DriveDesk integration idea. Later systems
such as accounting exports, bank imports, website forms, telephony, or messaging
providers can follow the same pattern: API creates a job, outbox stores it,
worker executes the adapter, and failures become visible operational state
instead of disappearing in logs.

The next layer is observability. `INTEGRATION_OBSERVABILITY.md` documents how
adapter jobs become Prometheus metrics, structured worker logs, and runbook
signals for retry and dead-letter handling.
