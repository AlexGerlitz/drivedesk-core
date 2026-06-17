# DriveDesk Workflow Action Runs

Workflow action runs are the execution history behind tenant-owned workflow
rules.

Workflow rules answer:

```text
when should automation run?
```

Workflow action runs answer:

```text
what did automation create?
```

## API Shape

```text
GET /tenants/{tenant_id}/workflow-action-runs
```

The endpoint returns tenant-owned history for matched workflow actions. A run can
link back to:

- the workflow rule;
- the source business record;
- the generated outbox event;
- the generated task record, when the action created human work.

## Example Flow

```text
contract draft -> approved
        |
        v
business_record.status_changed
        |
        v
workflow rule match
        |
        v
workflow.action_run.created
        |
        +--> workflow.contract_approved outbox event
        +--> workflow.task_record.created outbox event
        +--> workflow.contract_sync.requested outbox event
```

## Stored Links

Each run stores compact ids and lifecycle fields:

- `workflow_rule_id`;
- `trigger_event_type`;
- `action_type`;
- `status`;
- `source_record_id`;
- `source_record_type`;
- `previous_status`;
- `new_status`;
- `outbox_event_id`;
- `task_record_id`;
- `result_json`.

The first status is `created`.

## Why This Exists

This gives DriveDesk an operator-friendly execution trail:

- support can see what automation produced;
- an admin UI can show workflow history without parsing logs;
- metrics can count action volume without exposing payloads;
- incidents can be reviewed from database state even if logs are unavailable.

## Metrics

`/metrics` exposes aggregate workflow action run counts:

```text
drivedesk_workflow_action_runs{action_type="emit_outbox_event",status="created"} 1
drivedesk_workflow_action_runs{action_type="create_task_record",status="created"} 1
drivedesk_workflow_action_runs{action_type="request_adapter_sync",status="created"} 1
```

Metric labels are intentionally limited to:

- `action_type`;
- `status`.

Rule names, action payloads, tenant ids, user ids, record ids, record titles,
external references, and request bodies must not appear in metrics.

## Boundary

This is not a queue worker result table yet. It is the first stable execution
history contract for workflow actions created by business record transitions.

Future work can add richer statuses, retry attempts, duration, worker ownership,
and admin UI filtering.
