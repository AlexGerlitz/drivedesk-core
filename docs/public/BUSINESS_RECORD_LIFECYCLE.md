# DriveDesk Business Record Lifecycle

Business record lifecycle policies describe the normal status paths for core
tenant-owned records: contracts, payments, lessons, tasks, and documents.

The goal is to keep DriveDesk from becoming a generic table where any status can
mean anything. The platform exposes a small policy catalog and a read-only
preview endpoint so UI, workflow rules, and operators can understand whether a
status change is expected before changing data.

## Policy Catalog

```text
GET /business-record-lifecycle-policies
```

The catalog is public-safe metadata. It returns record types, initial statuses,
known statuses, terminal statuses, and allowed transition groups.

Example:

```json
{
  "record_type": "contract",
  "initial_status": "draft",
  "statuses": ["draft", "approved", "pending_signature", "active", "completed", "cancelled"],
  "terminal_statuses": ["completed", "cancelled"],
  "transitions": [
    {
      "from_status": "draft",
      "to_statuses": ["approved", "pending_signature", "cancelled"],
      "reason": "Contract can be approved, sent for signature, or cancelled before activation."
    }
  ]
}
```

## Transition Preview

```text
POST /tenants/{tenant_id}/business-records/lifecycle-preview
```

Request:

```json
{
  "record_type": "contract",
  "from_status": "draft",
  "to_status": "approved"
}
```

Response:

```json
{
  "record_type": "contract",
  "from_status": "draft",
  "to_status": "approved",
  "valid": true,
  "reason": "contract can move from draft to approved.",
  "allowed_next_statuses": ["approved", "pending_signature", "cancelled"],
  "terminal": false
}
```

The preview endpoint is tenant-scoped and requires `business_record:read`. It
does not mutate business records.

## Current Record Types

| Record type | Initial status | Terminal statuses |
| --- | --- | --- |
| `contract` | `draft` | `completed`, `cancelled` |
| `payment` | `pending` | `cancelled`, `refunded` |
| `lesson` | `scheduled` | `completed`, `cancelled` |
| `task` | `open` | `done`, `cancelled` |
| `document` | `draft` | `archived`, `cancelled` |

## Why This Exists

Lifecycle policy gives future UI and workflow automation a stable contract:

- render valid next actions;
- warn about impossible transitions;
- keep workflow rules aligned with domain state;
- document business behavior in OpenAPI and tests;
- avoid hiding business rules inside frontend conditionals.

## Boundary

This sprint exposes catalog and preview validation. The current transition
endpoint remains the mutation path:

```text
POST /tenants/{tenant_id}/business-records/{record_id}/transition
```

Future enforcement can reuse the same policy helper when the product is ready to
make invalid transitions hard failures.

## Human Explanation

For a real business platform, status is not just text. A payment, lesson,
contract, task, and document each have their own normal path. This layer makes
those paths explicit, testable, and visible through the API.
