# ADR-0068: Business Action Plan Preview

## Status

Accepted

## Context

DriveDesk can already normalize cross-system observations, preview detections,
open business exceptions, route escalations, and build role briefings.

The next product step is turning that context into ordered operator work. A user
should not have to inspect CRM, bank, accounting, exception, repair, and audit
screens separately before deciding what to do.

## Decision

Add a read-only action-plan preview:

```text
POST /tenants/{tenant_id}/business-action-plans/preview
```

The first plan kind is `exception_resolution`.

The preview composes existing tenant-scoped state into:

- work lanes;
- ordered steps;
- automation candidates;
- approval gates;
- review points;
- evidence links;
- API handoff points.

The preview does not create tasks, approve repairs, execute repairs, notify
users, enqueue outbox events, or mutate external systems.

## Consequences

- The public demo now shows the path from business problem to ordered operator
  work.
- External systems remain behind adapters, repair approvals, dry-run execution,
  and public-safe evidence.
- Future real provider adapters can reuse the same action-plan shape while
  changing only provider-specific checks and write operations.
