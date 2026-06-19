# Business Operations Control Tower

DriveDesk is moving from a generic workflow backend toward a business
operations control layer.

The first public-safe slice models a common cross-system failure:

1. CRM still says a deal is waiting for payment.
2. Bank evidence says payment was received.
3. Accounting export has not been sent.
4. DriveDesk previews the detected mismatch before mutating data.
5. DriveDesk opens a business exception.
6. DriveDesk previews escalation routing: owner, queue, SLA, and next action.
7. DriveDesk previews an ordered action plan for the responsible operator.
8. DriveDesk previews notification drafts without sending anything externally.
9. A repair action is proposed, approved, and executed in dry-run mode.
10. A role briefing turns the raw evidence into the next useful operator view.

This is intentionally not another workflow automation demo. The control tower
tracks business state across systems, detects an exception, records impact, and
keeps the repair path auditable.

## API Surface

| Step | Endpoint | Purpose |
| --- | --- | --- |
| Preview detections | `POST /tenants/{tenant_id}/business-detections/preview` | Detect exception candidates and suggested repair actions from observations without mutating data. |
| Preview escalations | `POST /tenants/{tenant_id}/business-escalations/preview` | Route open business exceptions to owner roles, queues, SLA targets, and next actions without mutating data. |
| Preview action plan | `POST /tenants/{tenant_id}/business-action-plans/preview` | Build ordered operator work, automation candidates, approval gates, and evidence links without mutating data. |
| Preview notifications | `POST /tenants/{tenant_id}/business-notifications/preview` | Build notification channel readiness, drafts, delivery plan, approval gates, and evidence without sending messages. |
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
| `BusinessEscalationPreview` | A read-only triage result with queue, owner role, SLA, next action, and evidence. |
| `BusinessActionPlanPreview` | A read-only work plan with lanes, ordered steps, automation candidates, approval gates, and evidence. |
| `BusinessNotificationPreview` | A read-only communication plan with channels, drafts, delivery plan, approval gates, and evidence. |
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

## Escalation Preview

The escalation preview is the triage step after an exception exists and before
an operator decides what to do next. The first policy is `exception_triage`.

It reads open business exceptions and linked repair actions, then returns:

- owner role, for example `accountant`;
- queue, for example `finance_reconciliation`;
- escalation level and SLA minutes;
- the next safe action, for example `execute_repair_dry_run`;
- evidence that ties the route back to the exception and repair action.

The preview is read-only. It does not create tasks, approve repairs, execute
repairs, enqueue outbox events, or notify external systems.

## Action Plan Preview

The action plan preview is the operator workbench step. It turns the routed
exception into ordered work for a role such as `accountant`.

It returns:

- work lane, for example `finance_reconciliation`;
- ordered steps such as evidence review, dry-run repair execution, and exception
  acknowledgement;
- automation candidates such as repair execution queueing and read-only
  accounting export recheck;
- approval gates showing whether repair approval is satisfied;
- evidence that ties the plan back to observations, exceptions, and repair
  actions.

The preview is read-only. It does not create tasks, notify users, enqueue
outbox events, approve repairs, execute repairs, or mutate external systems.

## Notification Preview

The notification preview is the communication step after the action plan is
ready. It turns ordered work into public-safe drafts for channels such as
`in_app` and `telegram`.

It returns:

- channel readiness;
- recipient role;
- draft title and body;
- action endpoint;
- delivery mode;
- approval gates;
- evidence labels.

The preview is read-only. It does not enqueue notification events, send
messages, call Telegram, call email providers, call CRM systems, or include raw
personal data in the public payload.

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
- one `exception_triage` escalation preview with owner, queue, SLA, and next
  action;
- one `exception_resolution` action plan with ordered steps, automation
  candidates, and approval gates;
- one `action_plan_updates` notification preview with in-app and Telegram draft
  boundaries;
- one approval-gated `sync_status` repair action;
- one accountant briefing with source systems, highlights, recommended actions,
  and review points;
- a five-step flow from observation to dry-run repair evidence.

Verification:

```bash
bash scripts/check_public_business_control_tower.sh
```
