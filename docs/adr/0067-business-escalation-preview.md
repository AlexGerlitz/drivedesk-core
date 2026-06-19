# ADR-0067: Business Escalation Preview

## Status

Accepted

## Context

Business detection can identify an exception candidate and business briefing can
summarize the current facts for a role. A real operations platform also needs a
triage step between those two views: who owns the issue, which queue should see
it, what SLA applies, and which existing repair endpoint should be used next.

The platform should add that routing layer without introducing premature task
creation, external notification writes, or a separate workflow service.

## Decision

Add a read-only escalation preview endpoint:

```text
POST /tenants/{tenant_id}/business-escalations/preview
```

The first policy is `exception_triage`. It reads tenant-scoped
`BusinessException` and `RepairAction` records and returns:

- routed queue summaries;
- owner role;
- escalation level;
- SLA minutes;
- next approval-gated repair action;
- evidence references;
- API links for follow-up.

The preview does not create tasks, approve repairs, execute repairs, enqueue
outbox events, or mutate external systems.

## Consequences

- Operators get a bridge from detected business exceptions to accountable work.
- The public demo now proves a fuller control-loop shape:
  observe -> detect -> escalate -> brief -> repair.
- Real task creation, external notifications, and workflow automation can later
  use the preview output as input while staying behind explicit write endpoints.
