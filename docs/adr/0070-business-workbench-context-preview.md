# ADR-0070: Business Workbench Context Preview

## Status

Accepted

## Context

DriveDesk is moving toward a single business workbench: operators should work
inside DriveDesk while external systems provide useful context in the
background. The public demo already records normalized observations from CRM,
bank, and accounting-like systems, detects business exceptions, builds action
plans, and prepares notification drafts.

The missing layer is the operator-facing context between raw observations and
the final action plan. A future Bitrix24, 1C, bank, KKT, website, or support
adapter should not leak raw provider payloads, credentials, or personal data
into the workbench.

## Decision

Add a read-only workbench context preview:

```text
POST /tenants/{tenant_id}/business-workbench-context/preview
```

The preview reads normalized DriveDesk observations and returns:

- role-specific context cards;
- safe facts and payload keys;
- suggested next actions inside DriveDesk;
- data-boundary checks for read-only source context, PII redaction, and secret
  isolation;
- evidence links back to observations, exceptions, and action-plan previews.

The preview does not call external providers, read secrets, enqueue outbox
events, or mutate provider state.

## Consequences

- The public demo now shows the path from external facts to operator work:
  context, detection, escalation, action plan, notification, briefing, and
  repair.
- The integration story becomes closer to the commercial product goal: DriveDesk
  can be the main workspace while Bitrix24, 1C, banks, and other systems act as
  adapters.
- Real provider adapters can later feed the same normalized observation model
  without changing the workbench contract.
