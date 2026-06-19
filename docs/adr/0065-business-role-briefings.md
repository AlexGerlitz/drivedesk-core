# ADR-0065: Business Role Briefings

## Status

Accepted

## Context

DriveDesk receives business state from multiple systems: CRM, bank statements,
accounting exports, support tools, and other adapters. A raw event stream is not
enough for daily work. Operators need a compact view that explains what changed,
why it matters, which evidence supports it, and what action should happen next.

## Decision

DriveDesk will expose business role briefings as a read-model over the Business
Operations Control Tower.

The first slice is:

- `POST /tenants/{tenant_id}/business-briefings/preview`;
- role context for `operator`, `accountant`, `manager`, `owner`, or `support`;
- tenant-scoped evidence from `BusinessStateObservation`, `BusinessException`,
  and `RepairAction`;
- source systems, highlights, recommended actions, review points, and API links;
- no database mutation and no external provider write during preview.

The briefing layer does not replace the source of truth. It composes the
current state into a role-specific work surface.

## Consequences

- DriveDesk can present useful context inside the product before building real
  provider-specific AI features.
- The same control tower data can serve accounting, operations, management, and
  support workflows.
- The public demo can show the commercial direction without exposing real
  customer data or secrets.
- Future adapter work can feed the briefing model without changing the operator
  UI contract.
