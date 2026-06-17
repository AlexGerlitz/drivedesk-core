# ADR-0030: Outbox Retry Recovery

## Status

Accepted

## Context

DriveDesk uses an outbox for asynchronous integration work. The worker can move
events through:

- `pending`;
- `processed`;
- `retry`;
- `dead_letter`.

This gives visibility, but operators also need a safe recovery path. After a
temporary provider outage, a fixed mapping, or a reviewed dead-letter incident,
support should be able to requeue a failed event without editing the database
manually.

## Decision

Add an operator recovery endpoint:

```text
POST /tenants/{tenant_id}/outbox-events/{event_id}/retry
```

The endpoint accepts:

```json
{
  "reason": "provider recovered",
  "reset_attempts": false
}
```

It only accepts events currently in `retry` or `dead_letter`.

When accepted, the event is moved back to `pending`:

- `last_error` is cleared;
- `last_duration_ms` is cleared;
- `next_retry_at` is cleared;
- `processed_at` is cleared;
- `dead_lettered_at` is cleared;
- `result_json` is cleared;
- attempts are preserved unless `reset_attempts` is true.

The previous status, attempts, error, retry time, dead-letter time, reset flag,
and operator reason are written to the audit log as:

```text
outbox_event.retry_requested
```

## Consequences

- Operators can recover failed integration jobs without direct database access.
- The worker keeps owning actual adapter execution.
- Successful events cannot be accidentally requeued through this endpoint.
- Metrics reflect the event's current state after recovery.
- The audit log preserves the previous failure context before the event is
  cleaned for a new worker attempt.
