# ADR-0064: Business Operations Control Tower

Status: accepted

## Context

DriveDesk is no longer scoped as a single vertical CRM. The product direction is
a business operations layer that connects existing systems, understands
cross-system state, detects exceptions, and proposes safe repairs.

Workflow automation tools can move data between systems, but they often do not
own the business question: is the operation actually healthy?

## Decision

Introduce a Business Operations Control Tower layer:

- `BusinessStateObservation` records normalized state from connected systems.
- `BusinessException` represents an operator-facing business problem with
  severity, impact, evidence, and status.
- `RepairAction` represents an approval-gated fix proposal.

The first public-safe scenario is a CRM/payment/accounting mismatch:

1. CRM deal state remains `invoice_sent`.
2. Bank state says `paid`.
3. Accounting export state is `not_exported`.
4. DriveDesk opens `crm_payment_mismatch`.
5. DriveDesk proposes and dry-runs `sync_status`.

All actions stay tenant-scoped and reuse audit, outbox, RBAC, metrics, and the
existing public-safe demo boundary.

## Consequences

- The product story shifts from generic workflow automation to business
  exception management and repair.
- Public evidence remains synthetic and does not perform external mutations.
- Future real adapters can use the same lifecycle while changing only the
  provider-specific execution boundary.
- Business SLOs can be added on top of exceptions and repair latency.

## Verification

```bash
bash scripts/check_public_business_control_tower.sh
bash scripts/check_public_demo_api.sh
```
