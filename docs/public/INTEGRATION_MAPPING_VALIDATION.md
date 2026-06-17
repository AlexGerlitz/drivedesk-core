# DriveDesk Integration Mapping Validation

DriveDesk validates tenant-owned integration connection mappings against the
runtime adapter catalog.

The validation path is:

```text
GET /integration-adapters
        |
        v
POST /tenants/{tenant_id}/integration-connections
        |
        v
adapter descriptor -> required_mapping_keys -> mapping JSON
```

Runtime mapping transform and preview are documented separately in
`INTEGRATION_MAPPING_TRANSFORM.md`.

## What Is Validated

Connection creation checks:

- the selected `adapter_key` exists in the runtime adapter catalog;
- the adapter supports tenant-owned connection profiles;
- every `required_mapping_keys` entry is present in the submitted mapping;
- mapping values are non-empty strings;
- the same mapping remains valid when a file-import job references the
  connection later.

For the public fake file-import adapter, the required mapping keys are:

```json
["external_id", "display_name"]
```

Example valid mapping:

```json
{
  "external_id": "lead_id",
  "display_name": "full_name"
}
```

## Failure Examples

Missing required mapping key:

```json
{
  "external_id": "lead_id"
}
```

Result:

```text
400 Missing mapping keys for file.import.fake: display_name
```

Empty mapping value:

```json
{
  "external_id": "lead_id",
  "display_name": ""
}
```

Result:

```text
400 Invalid mapping values for file.import.fake: display_name
```

Unsupported connection profile adapter:

```json
{
  "adapter_key": "internal.noop"
}
```

Result:

```text
400 Adapter does not support integration connections: internal.noop
```

## Why This Exists

This makes integration setup safer before real providers exist.

Without validation, DriveDesk could store a connection profile that looks valid
but fails only when a background worker tries to run it. With runtime mapping
validation, the platform rejects broken configuration at the API boundary and
keeps the outbox focused on retryable execution work rather than avoidable
configuration mistakes.

## Public Safety

The public docs and demo use synthetic field names only. Real provider payloads,
tenant-specific mapping values, connection names, credentials, and raw imported
files stay out of the public surface.
