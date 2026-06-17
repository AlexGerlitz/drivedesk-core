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

The first supported action is:

```text
emit_outbox_event
```

## Example

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

## Why This Exists

This proves that DriveDesk can be a system of action:

- business state changes are explicit;
- automation rules are tenant-owned;
- triggered actions are auditable;
- integrations receive work through the outbox instead of direct side effects;
- later workflow actions can add tasks, approvals, notifications, and adapter
  sync jobs.

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

Future sprints can add rule enable/disable, richer conditions, task creation,
notification actions, approval actions, and adapter-specific sync actions.
