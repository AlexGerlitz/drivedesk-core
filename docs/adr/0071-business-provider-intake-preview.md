# ADR-0071: Business Provider Intake Preview

## Status

Accepted

## Context

DriveDesk is designed to become the operating workspace that can receive facts
from many external systems: CRM, banks, accounting tools, support desks, file
imports, and future authenticated providers.

The existing business control tower already works with normalized observations.
The missing public-safe step is the contract between an external provider payload
and a DriveDesk observation.

## Decision

Add a read-only provider intake preview endpoint:

`POST /tenants/{tenant_id}/business-provider-intake/preview`

The endpoint accepts a provider key, source type, subject, external reference,
and provider payload. It returns:

- a normalized observation shape that could later be persisted;
- a safe payload subset;
- provider payload keys;
- dropped key names;
- data-boundary checks;
- next DriveDesk steps for observation recording, workbench context, and
  detection preview.

The preview does not persist data, enqueue outbox events, call provider APIs,
read provider secrets, return raw provider payload values, or mutate external
systems.

## Consequences

- Future Bitrix24, bank, accounting, support, and file-import adapters have a
  clear contract for producing DriveDesk facts.
- The public demo can show an external-system intake path without exposing real
  credentials or customer data.
- Provider payload handling is separated from workbench rendering and detection
  logic.
- A later write-enabled intake can reuse the normalized observation shape while
  keeping persistence, audit, and outbox behavior explicit.
