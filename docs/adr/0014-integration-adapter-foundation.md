# ADR-0014: Integration Adapter Foundation

Status: accepted

## Context

DriveDesk needs to connect to external systems without making provider-specific
payloads part of the core domain. The project already has a modular monolith,
outbox events, and a worker loop.

## Decision

Add the first adapter foundation:

- provider-neutral adapter result and execution error contract;
- fake file import adapter for public-safe testing;
- API endpoint that creates an integration outbox event;
- worker execution through adapter resolution;
- outbox statuses for `processed`, `retry`, and `dead_letter`;
- `next_retry_at`, `result_json`, and `dead_lettered_at` fields on outbox
  events.

## Consequences

- External integrations now have a concrete execution path.
- Temporary provider failures can be retried instead of dropped.
- Permanent failures become visible dead-letter state.
- Later adapters can reuse the same outbox and worker contract.
- The first adapter remains synthetic and public-safe.
