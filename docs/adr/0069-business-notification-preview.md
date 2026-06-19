# ADR-0069: Business Notification Preview

## Status

Accepted

## Context

DriveDesk can build an action plan for an operator, but business work often
needs a communication step: notify the responsible role, link the action, and
make the delivery boundary explicit.

The public surface must show this product shape without sending Telegram,
email, CRM, or other external provider messages.

## Decision

Add a read-only notification preview:

```text
POST /tenants/{tenant_id}/business-notifications/preview
```

The first notification kind is `action_plan_updates`.

The preview composes the current action plan into:

- channel readiness;
- notification drafts;
- delivery plan;
- approval gates;
- review points;
- evidence links.

The preview does not enqueue outbox events, send messages, call external
providers, or store credentials.

## Consequences

- The public demo shows a complete workbench path: detect, route, plan, prepare
  notifications, brief, and repair.
- Notification content stays public-safe and avoids raw personal data.
- Future private adapters can reuse the same preview contract before enabling
  real delivery through intentionally configured provider secrets.
