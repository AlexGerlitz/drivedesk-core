# ADR-0034: Integration Mapping Transform Preview

Status: accepted

## Context

Tenant-owned integration connections can now store safe adapter mappings, but a
mapping that is only validated is not enough. The worker must use the mapping
when it executes adapter jobs, and operators need a way to inspect the mapping
result before an import creates retryable or dead-letter work.

## Decision

DriveDesk Core maps external provider fields into adapter-owned canonical fields
inside the adapter boundary.

For the fake file-import adapter:

- `external_id` can be mapped from a source field such as `lead_id`;
- `display_name` can be mapped from a source field such as `full_name`;
- the worker executes the adapter against normalized records;
- the API exposes a read-only mapping preview endpoint:
  `POST /tenants/{tenant_id}/integration-mapping-preview`.

The preview endpoint accepts sample records and either a direct mapping payload
or a tenant-owned integration connection id. It returns accepted/rejected record
counts, normalized preview rows, and per-row validation errors without writing
business state or outbox events.

## Consequences

- Integration profiles are not just stored; they affect worker execution.
- Admin UI can validate import mappings before scheduling sync work.
- Failed imports should move left into operator review instead of becoming
  avoidable dead-letter events.
- Mapping preview remains tenant-scoped and uses existing tenant read
  permission checks.
- Public documentation can show the integration contract without exposing real
  provider payloads or production data.
