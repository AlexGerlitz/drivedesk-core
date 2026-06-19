# Notification Delivery

DriveDesk Core includes a public-safe notification delivery runtime contract.
It shows how notification intent moves from a safe draft into outbox, worker,
provider gate, retry, dead-letter, operator review, and observability without
calling external providers.

## Evidence

Machine-readable evidence:

```text
docs/public/evidence/notification-delivery.sanitized.json
infra/notifications/notification-delivery.sanitized.json
```

API surface:

```text
GET /demo/notification-delivery
GET /demo/public
GET /demo/business-notification-channels
```

The standalone endpoint is also embedded into the public demo payload as
`notificationDelivery`, so the API response, static fallback, generated OpenAPI
schema, and UI tables are verified as one contract.

Doc path marker: `docs/public/NOTIFICATION_DELIVERY.md`.

Verifier:

```bash
bash scripts/check_public_notification_delivery.sh
```

## Runtime Path

```text
safe draft
  -> policy check
  -> idempotent outbox event
  -> notification worker
  -> provider gate
  -> retry or dead-letter
  -> operator review
  -> metrics, logs, alert, and runbook
```

## Delivery Contract

The public contract records:

- channel adapter profiles for `in_app`, `telegram`, `email`, `sms`, and
  `webhook`;
- `notification.delivery.requested` outbox events with stable idempotency keys;
- worker queues for internal and external notification delivery;
- private provider gates for channels that need secrets or provider contracts;
- retry and dead-letter routing;
- operator review path;
- public-safe metrics, structured logs, and alert names.

## Boundary

The public demo does not:

- call Telegram, email, SMS, webhook, CRM, bank, accounting, or any provider;
- store browser tokens;
- expose server-side secret references;
- include raw provider payloads;
- include raw request bodies;
- include personal data;
- send external messages.

External delivery belongs to private server-side connector configuration and
release approval. The public runtime proves the shape of the delivery path and
the safety gates around it.

## Related Docs

- `docs/public/BUSINESS_NOTIFICATION_CHANNELS.md`
- `docs/public/OUTBOX_RECOVERY.md`
- `docs/public/OBSERVABILITY_DASHBOARD.md`
- `docs/public/ALERT_ROUTING_EVIDENCE.md`
- `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md`
- `docs/public/API_BACKED_DEMO.md`
