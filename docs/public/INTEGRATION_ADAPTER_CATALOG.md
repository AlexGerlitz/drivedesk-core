# DriveDesk Integration Adapter Catalog

DriveDesk exposes a public-safe adapter catalog:

```text
GET /integration-adapters
```

The catalog answers:

```text
which adapters can this DriveDesk runtime execute, and what contract do they expect?
```

## Why It Exists

Connection profiles let a tenant configure an adapter. The adapter catalog lets
the admin UI, generated clients, smoke tests, and reviewers discover the adapter
contract before creating a connection or enqueueing a job.

This removes hardcoded UI assumptions such as:

```text
file.import.fake is probably a file-import adapter
```

and replaces them with runtime metadata:

```json
{
  "key": "file.import.fake",
  "name": "Fake File Import",
  "status": "active",
  "direction": "inbound",
  "connection_profile_supported": true,
  "connection_profile_required": false,
  "required_mapping_keys": ["external_id", "display_name"]
}
```

## Catalog Fields

Each adapter descriptor includes:

| Field | Meaning |
| --- | --- |
| `key` | Stable adapter identifier used by outbox jobs and connection profiles. |
| `name` | Human-readable adapter name. |
| `status` | Runtime status such as `active`. |
| `category` | Adapter family, for example `file_import` or `internal`. |
| `direction` | Data direction, for example `inbound` or `internal`. |
| `purpose` | Short public-safe explanation. |
| `connection_profile_supported` | Whether tenant-owned connection profiles can point at this adapter. |
| `connection_profile_required` | Whether a job must provide a connection profile. |
| `payload_schema` | Public-safe payload shape expected by the adapter. |
| `config_example` | Safe example config shape. |
| `mapping_example` | Safe example field mapping. |
| `required_mapping_keys` | Mapping keys that must be present when a tenant connection profile is created. |
| `capabilities` | What the adapter proves. |
| `failure_modes` | Public-safe failure modes used for retry/dead-letter tests. |

## Current Runtime Adapters

The current catalog contains executable adapters only:

| Adapter | Direction | Connection Profile | Purpose |
| --- | --- | --- | --- |
| `file.import.fake` | `inbound` | supported | Synthetic file import adapter for contract tests and public demos. |
| `internal.noop` | `internal` | not supported | Internal acknowledgement path for default outbox events. |

Planned provider adapters can appear in product docs and public demo data, but
they should not appear in the runtime catalog until the worker can execute them.

## Relationship To Connection Profiles

The flow is:

```text
GET /integration-adapters
        |
        v
POST /tenants/{tenant_id}/integration-connections
        |
        v
POST /tenants/{tenant_id}/integration-imports/file
        |
        v
outbox -> worker -> adapter
```

The catalog is read-only. It does not store tenant data, connection names,
mapping values from real tenants, provider payloads, or sensitive provider
values.

## Public Verification

The public smoke test validates:

- `/integration-adapters` returns `file.import.fake` and `internal.noop`;
- OpenAPI includes `GET /integration-adapters`;
- the file-import descriptor exposes `connection_profile_supported`;
- the file-import descriptor exposes `required_mapping_keys`;
- the file-import descriptor includes mapping and payload examples;
- the public demo adapter cards include connection-profile metadata.
