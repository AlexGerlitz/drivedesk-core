# ADR-0028: Workflow Task and Adapter Sync Actions

## Status

Accepted

## Context

The first workflow rule foundation proved that a business record status change
can match tenant-owned rules and emit configured outbox events. That is useful,
but a platform workflow engine must also be able to create operational work and
request integration work through stable action types.

## Decision

Extend workflow rules with two additional action types:

```text
create_task_record
request_adapter_sync
```

`create_task_record` creates a tenant-owned `task` business record inside the
same transaction as the triggering business status transition. The created task
also writes the normal `business_record.created` audit and outbox events, plus a
workflow outbox event:

```text
workflow.task_record.created
```

`request_adapter_sync` enqueues a configured outbox event for adapter work. The
default event is:

```text
workflow.adapter_sync.requested
```

Each matching workflow action still writes:

```text
workflow.rule.triggered
```

## Consequences

- Workflow rules can now create human work, not only technical outbox messages.
- Adapter sync requests use the same retryable outbox path as other integration
  jobs.
- The API remains a modular monolith. No separate workflow service is introduced.
- Metrics remain aggregate-only through `drivedesk_workflow_rules`; task titles,
  action payloads, tenant ids, user ids, and record ids stay out of metric labels.
