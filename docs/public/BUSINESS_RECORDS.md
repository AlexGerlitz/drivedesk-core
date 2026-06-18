# DriveDesk Business Records

DriveDesk Core now includes a small tenant-owned business record foundation.
It is intentionally generic: the goal is to prove the platform boundary before
building detailed product modules.

## API Shape

```text
POST /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records
GET /tenants/{tenant_id}/business-records?record_type=contract
GET /business-record-lifecycle-policies
POST /tenants/{tenant_id}/business-records/lifecycle-preview
POST /tenants/{tenant_id}/business-records/{record_id}/transition
POST /tenants/{tenant_id}/workflow-rules
GET /tenants/{tenant_id}/workflow-rules
```

Supported public-safe record types:

- `contract`;
- `payment`;
- `lesson`;
- `task`;
- `document`.

## Why This Exists

The long-term platform needs contracts, payments, lessons, tasks, and
documents. Instead of adding five unfinished CRUD modules, this layer proves the
shared platform behavior once:

- tenant ownership through `tenant_id`;
- bearer-token tenant membership checks;
- explicit read/write permissions;
- audit events;
- outbox events;
- lifecycle transitions;
- aggregate Prometheus metrics.
- reusable tenant-owned repository helpers.
- lifecycle policy catalog and read-only transition preview.

## Verified Behavior

The Core API tests cover:

- a manager creating `contract` and `payment` records inside their tenant;
- listing all records for a tenant;
- filtering records by `record_type`;
- rejecting cross-tenant reads;
- rejecting viewer writes;
- writing `business_record.created` audit events;
- enqueuing `business_record.created` outbox events with
  `adapter_key=internal.business_record`.
- changing a record status through the transition endpoint;
- writing `business_record.status_changed` audit events;
- enqueuing `business_record.status_changed` outbox events with
  `adapter_key=internal.business_record`;
- triggering matching workflow rules through `workflow.rule.triggered`;
- enqueuing configured workflow outbox events such as
  `workflow.contract_approved`;
- creating task records through workflow action `create_task_record`;
- requesting adapter sync work through workflow action `request_adapter_sync`;
- recording workflow action runs through `workflow.action_run.created`;
- listing lifecycle policies for contracts, payments, lessons, tasks, and
  documents through `GET /business-record-lifecycle-policies`;
- previewing valid and invalid transitions through
  `POST /tenants/{tenant_id}/business-records/lifecycle-preview`;
- exposing aggregate metric rows such as:

```text
drivedesk_business_records{record_type="contract",status="approved"} 1
drivedesk_business_records{record_type="task",status="open"} 1
```

Matching workflow rule counts are exposed separately:

```text
drivedesk_workflow_rules{action_type="emit_outbox_event",status="active",trigger_event_type="business_record.status_changed"} 1
drivedesk_workflow_action_runs{action_type="emit_outbox_event",status="created"} 1
```

The business record metric labels are intentionally limited to `record_type` and
`status`.
Titles, external references, payload data, user identifiers, tenant identifiers,
rule names, workflow action payloads, and request bodies must not appear in
metrics.

## Boundary

This is not a final domain model for contracts, payments, lessons, tasks, or
documents. It is the first stable platform path for tenant-owned business data.

Future domain modules can move a record type into a dedicated table when it
needs its own lifecycle, validation rules, integrations, or reporting shape.

`BUSINESS_RECORD_LIFECYCLE.md` documents the current lifecycle policy catalog
and preview contract.
