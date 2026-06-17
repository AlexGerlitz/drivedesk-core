# ADR-0027: Workflow Rule Foundation

## Status

Accepted

## Context

DriveDesk Core already has tenant-owned business records, lifecycle transitions,
audit events, outbox events, and aggregate metrics. That proves that a user can
change business state, but it does not yet prove platform automation.

The platform needs a small workflow foundation that can react to domain state
changes without introducing a large workflow engine too early.

## Decision

Add tenant-owned workflow rules in `dd_workflow_rules`.

The first supported trigger is:

```text
business_record.status_changed
```

The first supported action is:

```text
emit_outbox_event
```

When a business record status transition matches an active workflow rule, the
API writes:

- a `workflow.rule.triggered` audit event;
- an outbox event configured by the rule.

Workflow rules are managed through:

```text
POST /tenants/{tenant_id}/workflow-rules
GET /tenants/{tenant_id}/workflow-rules
```

Rule configuration uses existing tenant read/write permission checks. This keeps
the first foundation small and avoids changing the RBAC policy surface in this
sprint.

## Observability

`/metrics` exposes aggregate workflow rule counts:

```text
drivedesk_workflow_rules{status="active",trigger_event_type="business_record.status_changed",action_type="emit_outbox_event"} 1
```

Metrics must not include rule names, action payloads, tenant ids, user ids,
business record ids, titles, external references, or request bodies.

## Consequences

- Business state changes can now trigger automated handoff through the same
  outbox path as integrations.
- Workflow execution is auditable.
- The foundation remains a modular monolith feature, not a separate workflow
  microservice.
- Future actions can add task creation, notifications, approvals, or adapter
  sync jobs without replacing the first rule table.
