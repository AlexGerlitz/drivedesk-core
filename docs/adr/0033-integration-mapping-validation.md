# ADR-0033: Integration Mapping Validation

## Status

Accepted

## Context

DriveDesk has a runtime adapter catalog and tenant-owned integration connection
profiles. The next risk is accepting connection mappings that are structurally
wrong and only fail later inside background jobs.

For a platform Integration Hub, broken setup should be rejected at the API
boundary when the configuration is created, not discovered after a worker has
already enqueued or retried work.

## Decision

Adapter descriptors define `required_mapping_keys`.

When `POST /tenants/{tenant_id}/integration-connections` creates a connection,
the API validates that:

- the adapter exists;
- the adapter supports tenant-owned connection profiles;
- the submitted mapping contains every required key;
- mapping values are non-empty strings.

File-import job creation re-validates the stored mapping before using a
connection profile. This protects the worker path from older or manually changed
invalid rows.

## Consequences

- Broken connection profiles are rejected before they reach outbox execution.
- Admin UI and generated clients can read mapping requirements from
  `GET /integration-adapters`.
- `internal.noop` remains executable for internal outbox events, but it is not a
  tenant-owned connection-profile adapter.
- Future adapters can add mapping requirements without creating provider-specific
  validation branches in the API layer.
