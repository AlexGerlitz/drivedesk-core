# ADR-0029: Workflow Action Run Observability

## Status

Accepted

## Context

Workflow rules can already react to `business_record.status_changed` and create
outbox events, task records, or adapter sync requests. That proves automation,
but it does not give operators a compact execution history.

For a production platform, support and incident review need to answer:

- which rule matched;
- which action type ran;
- which business record triggered it;
- which outbox event or task record was created;
- whether metrics can show action volume without exposing business payloads.

Raw logs are not enough because logs may rotate, be sampled, or be stored in a
different observability backend. The domain database needs a tenant-owned
execution record.

## Decision

Add `dd_workflow_action_runs` as a tenant-owned execution history table.

Each workflow action run stores:

- tenant id;
- workflow rule id;
- trigger event type;
- action type;
- execution status;
- source business record id and type;
- previous and new status;
- linked outbox event id, when one was created;
- linked task record id, when one was created;
- compact result JSON with ids only.

Each created run also writes `workflow.action_run.created` to the audit log.

Expose tenant-owned history through:

```text
GET /tenants/{tenant_id}/workflow-action-runs
```

Expose aggregate Prometheus metrics through:

```text
drivedesk_workflow_action_runs{action_type="emit_outbox_event",status="created"} 1
```

Metric labels must stay limited to `action_type` and `status`.

## Consequences

- Operators can trace automation effects without scraping raw logs.
- Workflow action history can be shown in admin UI later.
- Public portfolio reviewers can see a real execution-history layer behind the
  automation feature.
- Metrics stay aggregate-only and avoid rule names, tenant ids, user ids, record
  ids, titles, external references, action payloads, and request bodies.
- The first status is `created`; future worker-backed action execution can add
  `running`, `completed`, `failed`, and retry state if needed.
