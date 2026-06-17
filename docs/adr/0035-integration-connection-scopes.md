# ADR-0035: Integration Connection Scopes

Status: accepted

## Context

Tenant-owned integration connection profiles can store mapping and config. As
the Integration Hub grows, a single profile should not automatically be valid
for every operation supported by an adapter.

For example, an admin may need a profile that can preview imported rows, while a
worker needs a profile that can execute the import job.

## Decision

Adapter descriptors declare connection scopes:

- `supported_connection_scopes`;
- `default_connection_scopes`.

For `file.import.fake`, the supported scopes are:

- `file_import:preview`;
- `file_import:execute`.

Connection creation validates requested scopes against the runtime adapter
descriptor. If no scopes are provided, DriveDesk stores the adapter defaults.

The API enforces scopes at use time:

- `POST /tenants/{tenant_id}/integration-mapping-preview` requires
  `file_import:preview` when a stored connection is referenced;
- `POST /tenants/{tenant_id}/integration-imports/file` requires
  `file_import:execute` when a stored connection is referenced.

## Consequences

- Integration profiles become least-privilege runtime objects.
- A preview-only profile cannot accidentally enqueue import work.
- An execute-only profile cannot be used for operator preview screens.
- The adapter catalog remains the source of truth for supported scopes.
- Public docs can show the access model without exposing real provider
  credentials or production connection names.
