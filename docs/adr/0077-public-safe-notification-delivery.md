# ADR-0077: Public-Safe Notification Delivery Runtime

## Status

Accepted

## Context

DriveDesk already exposes a public-safe notification channel matrix. The next
contract needs to show how a delivery intent moves through runtime components:
draft preparation, policy checks, outbox enqueue, worker dispatch, provider
gate, retry, dead-letter, operator review, and observability.

The public surface must prove that runtime shape without calling Telegram,
email, SMS, webhook, CRM, bank, accounting, or any other provider.

## Decision

DriveDesk will expose a public-safe Notification Delivery contract through:

- `docs/public/NOTIFICATION_DELIVERY.md`;
- `docs/public/evidence/notification-delivery.sanitized.json`;
- `infra/notifications/notification-delivery.sanitized.json`;
- `GET /demo/notification-delivery`;
- `GET /demo/public` under `notificationDelivery`;
- `scripts/check_public_notification_delivery.sh`.

The contract records channel adapter profiles, delivery stages, outbox events,
retry policy, dead-letter plan, observability signals, API links, and data
boundaries.

## Consequences

- The public repository can prove notification delivery design without real
  provider calls or private credentials.
- Runtime evidence stays connected to outbox, worker, retry, dead-letter,
  alerting, and runbook surfaces.
- Credentials, browser tokens, raw request bodies, raw logs, private addresses,
  and customer data remain outside the public export.
