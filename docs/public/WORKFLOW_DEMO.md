# DriveDesk Workflow Demo

This document explains the public-safe synthetic workflow shown in the
DriveDesk Core demo.

The workflow is fake-data only. It exists to show the engineering shape of a
real business process without exposing private operations, customers,
infrastructure, credentials, or production data.

## Scenario

The demo follows one operational path:

```text
lead -> student -> contract -> audit -> outbox -> integration sync
```

It also exposes one reviewable end-to-end scenario:

```text
approval -> notification -> adapter -> incident -> recovery -> proof
```

That means DriveDesk does not only display records. It models the work as a
sequence of state changes, evidence, events, and integration handoff.

## Payload Contract

`GET /demo/public` returns the workflow in the same payload used by the public
demo shell.

Important fields:

| Field | Purpose |
| --- | --- |
| `workflow` | Current workflow state, owner, and stages. |
| `workflow.stages` | Human-readable business steps and their evidence. |
| `workflowScenarios` | Reusable automation scenarios with trigger, action type, outputs, and evidence. |
| `endToEndScenario` | One connected operational chain from approval to public proof evidence. |
| `timeline` | Ordered user-facing activity history. |
| `domainEvents` | Internal event stream between platform components. |
| `auditEvents` | Reviewable action log. |
| `outbox` | Async handoff state for integration work. |
| `integrationJobs` | Adapter job visibility, including retry and dead-letter examples. |

## Workflow Stages

The current synthetic flow has five stages:

1. `lead_created` - a new lead is captured by an adapter.
2. `student_created` - staff accept the lead and create a student record.
3. `contract_ready` - the platform prepares a contract draft.
4. `audit_recorded` - the state change is recorded for review.
5. `student_sync` - the outbox queues a future integration sync.

The final stage is intentionally shown as current, not completed. That makes
the demo more realistic: some work is done immediately, and some work waits for
background processing or an external system.

## Reusable Workflow Scenarios

The demo also includes scenario-level automation examples under
`workflowScenarios`. They use the same workflow engine shape documented in
`WORKFLOW_RULES.md` and `WORKFLOW_ACTION_RUNS.md`.

| Scenario | Trigger | Action type | Outputs | Evidence |
| --- | --- | --- | --- | --- |
| Contract approval sync | `business_record.status_changed contract:draft->approved` | `emit_outbox_event` | `audit_event`, `outbox_event`, `action_run` | `workflow.contract_approved` |
| Signature task creation | `business_record.status_changed contract:approved->signature_required` | `create_task_record` | `audit_event`, `task_record`, `action_run` | `workflow.task_record.created` |
| Accounting export request | `business_record.status_changed contract:approved->ready_for_billing` | `request_adapter_sync` | `outbox_event`, `integration_job`, `action_run` | `workflow.contract_sync.requested` |

These scenarios are deliberately small. The important part is that a business
state change can produce different controlled effects without bypassing audit,
action-run history, outbox delivery, or operator-visible evidence.

## End-To-End Scenario

The demo includes `endToEndScenario` so one complete synthetic chain can be
followed across the product and operations layers.

| Step | Owner | State | Evidence |
| --- | --- | --- | --- |
| Approval | Operations | `processed` | `workflow.contract_approved` |
| Notification | Workflow engine | `ready` | `notification.manager_signature_task.created` |
| Adapter | Integration hub | `retry` | `integration.accounting_export.requested` |
| Incident | Operator | `acknowledged` | `integration.incident.status_changed` |
| Recovery | Operator | `resolved` | `postcheck.gates.passed` |
| Proof | Release gate | `validated` | `docs/public/ENGINEERING_PROOF.md` |

This is intentionally synthetic. The value is the contract shape: workflow
automation can produce notifications and adapter work, adapter failures can
become operator-visible incidents, incidents can be recovered through runbooks,
and the result can be tied back to public-safe proof artifacts.

## Engineering Value

This small workflow proves several platform ideas at once:

- the UI can render business state from a backend-owned contract;
- the API owns the synthetic workflow payload;
- reusable workflow scenarios can be represented as trigger -> action ->
  outputs -> evidence;
- one end-to-end scenario connects approval, notification, adapter execution,
  incident response, recovery, and proof evidence;
- domain events are separate from user-facing timeline entries;
- audit and outbox are visible parts of the product model;
- integration work is treated as retryable background work;
- the same payload works in static fallback and API-backed mode.

## Engineering Summary

DriveDesk models the process instead of only displaying records. A lead becomes
a student, the contract step produces evidence, the audit trail records the
change, workflow scenarios describe reusable automation, and the outbox prepares
an integration sync. The end-to-end scenario then shows how workflow output
flows into notification, adapter, incident, recovery, and evidence layers. That
is the foundation for larger automation later.
