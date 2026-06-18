# Integration Connection Scopes

DriveDesk integration connection profiles are scoped.

Scopes answer:

```text
what is this connection profile allowed to do?
```

The runtime adapter catalog exposes two fields:

```json
{
  "supported_connection_scopes": ["file_import:execute", "file_import:preview"],
  "default_connection_scopes": ["file_import:execute", "file_import:preview"]
}
```

## File Import Scopes

The public fake file-import adapter supports:

| Scope | Meaning |
| --- | --- |
| `file_import:preview` | Can preview mapped rows before scheduling work. |
| `file_import:execute` | Can enqueue and execute file-import work. |

If a client creates a connection without an explicit `scopes` list, DriveDesk
stores the adapter defaults.

```json
{
  "name": "Demo file import profile",
  "adapter_key": "file.import.fake",
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  }
}
```

Stored result:

```json
{
  "scopes_json": "[\"file_import:execute\", \"file_import:preview\"]"
}
```

## Preview-Only Profile

```json
{
  "name": "Preview-only import profile",
  "adapter_key": "file.import.fake",
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  },
  "scopes": ["file_import:preview"]
}
```

This profile can call:

```text
POST /tenants/{tenant_id}/integration-mapping-preview
```

It cannot enqueue file-import work.

```text
409 Integration connection for file.import.fake lacks required scope: file_import:execute
```

## Execute-Only Profile

```json
{
  "name": "Execute-only import profile",
  "adapter_key": "file.import.fake",
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  },
  "scopes": ["file_import:execute"]
}
```

This profile can call:

```text
POST /tenants/{tenant_id}/integration-imports/file
```

It cannot be used for the mapping preview endpoint.

```text
409 Integration connection for file.import.fake lacks required scope: file_import:preview
```

## Invalid Scope

If a connection requests a scope not supported by the selected adapter, DriveDesk
rejects the profile at creation time.

```text
400 Unsupported connection scopes for file.import.fake: accounting:export
```

## Accounting Export Scope

The mock accounting export adapter supports:

| Scope | Meaning |
| --- | --- |
| `accounting:export` | Can enqueue and execute synthetic accounting document export work. |

```json
{
  "name": "Demo accounting export profile",
  "adapter_key": "accounting.export.mock",
  "config": {
    "provider": "mock-accounting",
    "mode": "synthetic"
  },
  "scopes": ["accounting:export"]
}
```

This profile can call:

```text
POST /tenants/{tenant_id}/integration-exports/accounting
```

It cannot be used for file-import work because the endpoint verifies adapter
compatibility before enqueueing an outbox event.

## What This Proves

- adapter descriptors control connection capabilities;
- connection profiles are least-privilege objects;
- API endpoints enforce scopes at use time;
- scope labels stay public-safe and do not expose tenant ids, provider payloads,
  credentials, or real connection names.
