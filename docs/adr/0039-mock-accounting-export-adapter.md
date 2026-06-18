# ADR-0039: Mock Accounting Export Adapter

## Status

Accepted

## Context

DriveDesk already has an inbound integration path through `file.import.fake`:
tenant-owned connection profiles, mapping validation, outbox enqueueing, worker
execution, retry/dead-letter handling, metrics, and operator review.

The Integration Hub also needs a public-safe outbound example. Future real
providers can include accounting systems, online cash registers, banks, and ERP
systems, but those integrations must not expose private provider payloads,
credentials, or business data in the public repository.

## Decision

Add `accounting.export.mock` as an executable outbound adapter.

The adapter:

- declares an operation contract named `accounting_export_execute`;
- uses event type `accounting.export.requested`;
- is triggered by `POST /tenants/{tenant_id}/integration-exports/accounting`;
- requires the `accounting:export` connection scope when a connection profile is
  used;
- runs through the existing outbox worker;
- supports retryable and permanent failure simulation;
- appears in the existing operator review queue with a redacted payload summary.

## Consequences

- The public demo now proves both inbound and outbound adapter contracts.
- The core remains a modular monolith; no new service boundary is introduced.
- Future provider adapters can reuse the same outbox, retry, metrics, and
  operator-review behavior.
- Public docs remain safe because only synthetic document summaries are shown.
