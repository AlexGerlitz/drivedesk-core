# Business Notification Channels

This document describes the public-safe notification channel matrix for
DriveDesk Core.

The matrix shows how DriveDesk can prepare operator communication across
multiple channels while keeping the public demo read-only:

```text
internal action
  -> channel readiness matrix
  -> safe delivery drafts
  -> approval and secret gates
  -> no external delivery in public demo
```

## Public Contract

The contract is exposed through:

- `GET /demo/public` as `businessNotificationChannels`;
- `GET /demo/business-notification-channels` as a standalone public demo payload;
- `POST /tenants/{tenant_id}/business-notification-channels/preview` as the
  tenant API preview.

The public payload covers:

- `in_app` as the internal-ready channel;
- `telegram`, `email`, `sms`, and `webhook` as draft-only channels that require
  private connector and secret setup;
- safe delivery drafts with role, subject key, action summary, channel, and
  evidence labels only;
- content review, private channel setup, and external delivery gates;
- explicit data boundaries for no delivery, server-side secrets, and safe
  notification payloads.

## Boundaries

The public demo does not:

- enqueue notification delivery outbox rows;
- call Telegram, email, SMS, webhook, CRM, bank, or accounting providers;
- store browser tokens;
- include raw provider payloads;
- include personal data;
- send external messages.

External channel credentials belong to private server-side connector
configuration. The public matrix only proves how DriveDesk evaluates readiness
and prepares safe drafts.

## Verification

```bash
bash scripts/check_public_business_notification_channels.sh
bash scripts/check_public_demo_api.sh
```

The checker verifies the API payload, static fallback, OpenAPI schema, public
demo UI, export gate wiring, and public-safe documentation references.

## Related Docs

- `docs/public/BUSINESS_NOTIFICATION_CHANNELS.md` - this contract.
- `docs/public/BUSINESS_TASK_HANDOFF.md` - upstream task handoff contract.
- `docs/public/API_BACKED_DEMO.md` - public demo API contract.
- `docs/public/PROVIDER_CONNECTOR_GUIDE.md` - future private connector path.
