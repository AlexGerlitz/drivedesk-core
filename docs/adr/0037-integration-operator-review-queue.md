# ADR-0037: Integration Operator Review Queue

Status: accepted

## Context

DriveDesk integrations already use outbox jobs, retry state, dead-letter state,
structured adapter operation contracts, and audited retry requests. Operators
still need a safe way to see which integration jobs require attention without
opening raw payloads, database rows, or worker logs.

Future adapters for 1C, banks, KKT, webhooks, and file imports will need the
same operator workflow: inspect failure, understand the operation boundary,
confirm the recovery action, then retry through an audited endpoint.

## Decision

Add a tenant-scoped read-only operator review queue:

```text
GET /tenants/{tenant_id}/integration-operator-review
```

The endpoint lists only integration outbox events in `retry` or `dead_letter`.
It returns safe operational fields: adapter key, operation key, event type,
status, severity, attempts, last error, required connection scope, redacted
payload summary, recommended action, and the retry endpoint.

It does not return raw records, source names, provider credentials, config
values, mapping values, request bodies, or tenant-specific provider payloads.

Recovery remains a separate audited action:

```text
POST /tenants/{tenant_id}/outbox-events/{event_id}/retry
```

## Consequences

- Operators get a review surface for failed integrations.
- The UI can render review cards without parsing outbox payloads directly.
- The retry action remains explicit and audited through
  `outbox_event.retry_requested`.
- Adapter operation contracts become useful for runtime support screens, not
  only documentation.
- The endpoint improves incident response without adding a new database table or
  new policy category.
