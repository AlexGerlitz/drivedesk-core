# Business Operations Control Tower

DriveDesk is moving from a generic workflow backend toward a business
operations control layer.

The first public-safe slice models a common cross-system failure:

1. CRM still says a deal is waiting for payment.
2. Bank evidence says payment was received.
3. Accounting export has not been sent.
4. DriveDesk previews the detected mismatch before mutating data.
5. DriveDesk opens a business exception.
6. A repair action is proposed, approved, and executed in dry-run mode.
7. A role briefing turns the raw evidence into the next useful operator view.

This is intentionally not another workflow automation demo. The control tower
tracks business state across systems, detects an exception, records impact, and
keeps the repair path auditable.

## API Surface

| Step | Endpoint | Purpose |
| --- | --- | --- |
| Preview detections | `POST /tenants/{tenant_id}/business-detections/preview` | Detect exception candidates and suggested repair actions from observations without mutating data. |
| Preview briefing | `POST /tenants/{tenant_id}/business-briefings/preview` | Build a role-specific work briefing from observations, exceptions, and repair actions without mutating data. |
| Observe state | `POST /tenants/{tenant_id}/business-state/observations` | Record a normalized state sample from CRM, bank, accounting, support, or another connected system. |
| List observations | `GET /tenants/{tenant_id}/business-state/observations` | Review the tenant-scoped state timeline for a subject. |
| Open exception | `POST /tenants/{tenant_id}/business-exceptions` | Convert inconsistent observations into a business-level exception with severity, impact, and evidence. |
| List exceptions | `GET /tenants/{tenant_id}/business-exceptions` | Show the operator queue of business problems. |
| Propose repair | `POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions` | Create a safe repair action linked to an exception. |
| Approve repair | `POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/approve` | Record human approval before execution. |
| Execute repair | `POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute` | Queue the repair execution request and store dry-run result evidence. |

## Data Model

| Model | Meaning |
| --- | --- |
| `BusinessDetectionPreview` | A read-only detector result with matched rules, exception candidates, repair suggestions, and evidence. |
| `BusinessBriefing` | A read-model for the current operator role, subject, evidence, risks, and next actions. |
| `BusinessStateObservation` | One normalized fact from an external system. |
| `BusinessException` | A business problem derived from observations. |
| `RepairAction` | A proposed and auditable fix for an exception. |

The models are tenant-scoped and use the same audit/outbox foundation as the
rest of the API.

## Role Briefing

The briefing endpoint is the practical bridge between integrations and daily
work. For example, an accountant can open a payment mismatch and see:

- which systems contributed evidence;
- what exception is still open;
- why the issue matters for accounting export;
- which repair action is ready;
- which endpoint or workflow should be used next.

The preview is read-only. It does not create records, approve repairs, or write
to external systems. It composes the current tenant-scoped state into a compact
work surface.

## Detection Preview

The detection preview is the automatic step before a real exception is created.
The first public-safe rule set is `payment_reconciliation`.

It matches:

- CRM says `invoice_sent`;
- bank says `paid`;
- accounting says `not_exported`.

It returns:

- a `crm_payment_mismatch` exception candidate;
- source observation evidence;
- a suggested approval-gated `sync_status` repair action;
- API links for committing the exception, repair, and role briefing.

The preview is read-only. It does not create `BusinessException`,
`RepairAction`, or outbox records.

## Safety Boundary

The public demo does not write to real external systems. Repair execution stores
a dry-run result and queues an outbox event with `external_mutation=false`.

That gives the project a realistic production shape without hiding unsafe
side effects behind a demo button.

## Metrics

The new layer exposes aggregate, label-safe metrics:

- `drivedesk_business_state_observations`
- `drivedesk_business_exceptions`
- `drivedesk_repair_actions`

The metrics avoid raw subject identifiers, customer names, payment references,
phone numbers, and document data.

## Public Demo

The public demo includes a `businessControlTower` payload with:

- synthetic observations from `crm.bitrix24.mock`, `bank.statement.mock`, and
  `accounting.export.mock`;
- one `payment_reconciliation` detection preview;
- one `crm_payment_mismatch` exception;
- one approval-gated `sync_status` repair action;
- one accountant briefing with source systems, highlights, recommended actions,
  and review points;
- a five-step flow from observation to dry-run repair evidence.

Verification:

```bash
bash scripts/check_public_business_control_tower.sh
```
