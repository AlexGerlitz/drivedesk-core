# ADR-0066: Business Detection Preview

## Status

Accepted

## Context

DriveDesk should not only display state from connected systems. The platform
needs to detect useful business exceptions automatically: for example, when CRM
still waits for payment, bank evidence says payment arrived, and accounting
export is blocked.

The first implementation must be public-safe, deterministic, and reviewable.

## Decision

DriveDesk will expose a read-only business detection preview endpoint:

- `POST /tenants/{tenant_id}/business-detections/preview`;
- initial rule set: `payment_reconciliation`;
- input source: tenant-scoped `BusinessStateObservation` records;
- output: detected exception candidates, suggested repair actions, source
  evidence, active rules, and next API links;
- no `BusinessException` or `RepairAction` is created during preview;
- no external provider write is performed during preview.

The first detector recognizes this pattern:

- CRM state is `invoice_sent`, `awaiting_payment`, or `unpaid`;
- bank state is `paid`, `settled`, or `captured`;
- accounting state is `not_exported`, `waiting_for_crm_status`, or
  `export_pending`.

When the pattern is found, DriveDesk returns a `crm_payment_mismatch` candidate
and suggests an approval-gated `sync_status` repair action.

## Consequences

- The product moves from manual exception entry toward automatic business
  supervision.
- The detection result remains explainable because every candidate includes
  source observations and the rule that matched.
- Real adapters such as Bitrix24, bank statements, and accounting exports can
  feed the same observation model later without changing the detection API.
- The commit step remains explicit: operators still decide when to create a
  real exception, approve repair, or execute a repair request.
