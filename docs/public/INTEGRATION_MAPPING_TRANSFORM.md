# Integration Mapping Transform

DriveDesk integration mappings are used at runtime, not only stored as profile
metadata.

The first executable example is the synthetic file-import adapter:

```json
{
  "adapter_key": "file.import.fake",
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  }
}
```

This means incoming rows can use provider-shaped fields:

```json
{
  "lead_id": "lead_001",
  "full_name": "Demo Learner One"
}
```

The worker normalizes that row before executing the adapter:

```json
{
  "external_id": "lead_001",
  "display_name": "Demo Learner One"
}
```

## Preview Endpoint

```text
POST /tenants/{tenant_id}/integration-mapping-preview
```

The endpoint is read-only. It does not create business records, outbox events,
or worker jobs.

Example request:

```json
{
  "adapter_key": "file.import.fake",
  "mapping": {
    "external_id": "lead_id",
    "display_name": "full_name"
  },
  "records": [
    {
      "lead_id": "lead_001",
      "full_name": "Demo Learner One"
    },
    {
      "lead_id": "lead_002",
      "full_name": ""
    }
  ]
}
```

Example response:

```json
{
  "adapter_key": "file.import.fake",
  "required_mapping_keys": ["external_id", "display_name"],
  "records_received": 2,
  "records_accepted": 1,
  "records_rejected": 1,
  "records": [
    {
      "index": 1,
      "status": "accepted",
      "normalized": {
        "external_id": "lead_001",
        "display_name": "Demo Learner One"
      },
      "errors": []
    },
    {
      "index": 2,
      "status": "rejected",
      "normalized": {
        "external_id": "lead_002",
        "display_name": ""
      },
      "errors": ["missing mapped value: display_name"]
    }
  ]
}
```

## Connection-Based Preview

The same endpoint can preview a stored tenant-owned connection:

```json
{
  "adapter_key": "file.import.fake",
  "integration_connection_id": "connection-id",
  "records": [
    {
      "lead_id": "lead_001",
      "full_name": "Demo Learner One"
    }
  ]
}
```

When a connection id is present, DriveDesk loads the stored mapping from that
connection, verifies tenant ownership, and checks that the connection has the
`file_import:preview` scope before returning the preview.

## Worker Behavior

File-import outbox payloads carry the selected `integration_connection_id` and
mapping JSON. The worker executes `file.import.fake` against normalized records,
so provider-shaped rows can be accepted as long as the profile mapping is valid.
When a stored connection is used, the API requires the `file_import:execute`
scope before creating outbox work.

## What This Proves

- adapter mappings are executable runtime behavior;
- admins can detect bad imports before scheduling work;
- mapping failures are visible as operator feedback instead of avoidable
  dead-letter jobs;
- the adapter boundary owns provider-specific field names.
