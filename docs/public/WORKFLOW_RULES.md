# DriveDesk Workflow Rules

DriveDesk Core now includes a small tenant-owned workflow rule foundation.
It is intentionally narrow: the goal is to prove event-driven automation before
adding a full workflow engine.

## API Shape

```text
POST /tenants/{tenant_id}/workflow-rules
GET /tenants/{tenant_id}/workflow-rules
```

The first supported trigger is:

```text
business_record.status_changed
```

Supported actions are:

```text
emit_outbox_event
create_task_record
request_adapter_sync
```

## Outbox Event Example

A tenant owner can create a rule like this:

```json
{
  "name": "Contract approval sync",
  "record_type": "contract",
  "from_status": "draft",
  "to_status": "approved",
  "action_config": {
    "event_type": "workflow.contract_approved",
    "adapter_key": "internal.workflow",
    "payload": {
      "next_step": "prepare_signature"
    }
  }
}
```

When a matching contract moves from `draft` to `approved`, DriveDesk writes:

- `business_record.status_changed` audit and outbox events;
- `workflow.rule.triggered` audit event;
- configured outbox event, for example `workflow.contract_approved`.

## Task Action Example

`create_task_record` creates a tenant-owned task business record when the rule
matches:

```json
{
  "name": "Create signature task",
  "record_type": "contract",
  "from_status": "draft",
  "to_status": "approved",
  "action_type": "create_task_record",
  "action_config": {
    "title": "Prepare signature package",
    "status": "open",
    "payload": {
      "assignee_role": "manager",
      "checklist": "signature"
    }
  }
}
```

When it runs, DriveDesk creates a `task` business record, writes the normal
`business_record.created` audit/outbox events, and enqueues:

```text
workflow.task_record.created
```

## Adapter Sync Example

`request_adapter_sync` creates a retryable outbox request for an integration
adapter:

```json
{
  "name": "Request accounting sync",
  "record_type": "contract",
  "from_status": "draft",
  "to_status": "approved",
  "action_type": "request_adapter_sync",
  "action_config": {
    "event_type": "workflow.contract_sync.requested",
    "adapter_key": "accounting.fake",
    "payload": {
      "target": "accounting"
    }
  }
}
```

This keeps adapter work behind the same outbox retry/dead-letter path used by
the integration layer.

## Why This Exists

This proves that DriveDesk can be a system of action:

- business state changes are explicit;
- automation rules are tenant-owned;
- triggered actions are auditable;
- integrations receive work through the outbox instead of direct side effects;
- workflow rules can create human work through task records;
- workflow rules can request adapter work without directly calling providers;
- later workflow actions can add approvals, notifications, and richer sync jobs.

## Metrics

`/metrics` exposes aggregate workflow rule counts:

```text
drivedesk_workflow_rules{action_type="emit_outbox_event",status="active",trigger_event_type="business_record.status_changed"} 1
```

The metric labels are intentionally limited to `status`, `trigger_event_type`,
and `action_type`.

Rule names, action payloads, tenant ids, user ids, record ids, titles, external
references, and request bodies must not appear in metrics.

## Boundary

This is not a final BPMN engine or low-code automation builder. It is the first
stable platform contract for:

```text
domain event -> rule match -> audit -> outbox handoff
```

Future sprints can add rule enable/disable, richer conditions, notification
actions, approval actions, and adapter-specific mapping configuration.
