# DriveDesk Outbox Recovery

Outbox recovery is the operator path for failed integration work.

The worker moves integration jobs into `retry` for temporary failures and
`dead_letter` for failures that need review. Recovery lets an operator put a
reviewed event back into the worker queue without editing the database by hand.

## API Shape

```text
POST /tenants/{tenant_id}/outbox-events/{event_id}/retry
```

Before retrying, operators can inspect failed integration jobs through:

```text
GET /tenants/{tenant_id}/integration-operator-review
```

That read-only review endpoint shows operation key, status, attempts, last
error, required connection scope, redacted payload summary, recommended action,
and the retry endpoint. It does not return raw records or provider payloads.

Request body:

```json
{
  "reason": "provider recovered",
  "reset_attempts": false
}
```

The endpoint accepts only:

- `retry`;
- `dead_letter`.

It rejects `pending` and `processed` events.

## State Change

Accepted recovery requests move the event back to:

```text
pending
```

The event is prepared for worker execution:

- `last_error` is cleared;
- `last_duration_ms` is cleared;
- `next_retry_at` is cleared;
- `processed_at` is cleared;
- `dead_lettered_at` is cleared;
- `result_json` is cleared;
- `attempts` are preserved unless `reset_attempts=true`.

## Audit Event

Every recovery request writes:

```text
outbox_event.retry_requested
```

The audit event stores the previous status, previous attempt count, previous
error, previous retry/dead-letter timestamps, reset flag, and operator reason.

## Why This Exists

This is a production-shaped recovery loop:

```text
worker failure -> retry/dead_letter -> operator review -> retry request -> pending -> worker execution
```

It avoids direct database edits, keeps adapter execution inside the worker, and
leaves a tenant-scoped audit trail for support and incident review.

## Metrics

Recovery changes the current outbox status, so existing aggregate metrics show
the new state:

```text
drivedesk_outbox_events{status="pending"} 2
drivedesk_integration_jobs{adapter_key="file.import.fake",status="pending"} 2
```

Metrics remain aggregate-only. They do not include event ids, tenant ids,
operator ids, provider payloads, file contents, errors, or recovery reasons.

## Boundary

This endpoint does not edit event payloads and does not call external providers
directly. It only requeues a reviewed event. The worker remains responsible for
adapter execution, retry, and dead-letter state.
