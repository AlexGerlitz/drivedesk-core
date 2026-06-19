# Business Task Handoff

DriveDesk can preview how an approved action plan becomes internal operator
work:

```text
action plan -> internal task cards -> internal outbox candidates -> notification drafts
```

The public contract is exposed in three places:

- `GET /demo/public` as `businessTaskHandoff`;
- `GET /demo/business-task-handoff` as a standalone public demo payload;
- `POST /tenants/{tenant_id}/business-task-handoffs/preview` as the tenant API preview.

The preview is intentionally read-only. It does not create business task
records, insert outbox rows, send notifications, call external providers, or
write to CRM, bank, accounting, Telegram, email, or any other system.

## Current Synthetic Path

The public demo turns a payment mismatch action plan into accountant-facing
work:

| Stage | Public-safe output | Boundary |
| --- | --- | --- |
| Action plan step | `review_detected_exceptions` task card | `would_create` only |
| Repair step | `execute_repair_dry_run` task card | approval remains required |
| Outbox handoff | `task.created` candidate | `internal.noop` only |
| Notification handoff | in-app draft | no external delivery |

Each task card includes only a role, subject key, source action, priority,
approval marker, and evidence label.

## Data Boundary

The handoff returns only safe facts:

- no raw provider payloads;
- no credentials;
- no phone numbers;
- no names;
- no persisted task records;
- no inserted outbox rows;
- no external notification delivery;
- no external provider writes.

The outbox candidates use `internal.noop` and `safe_task_reference` to show the
event shape without exposing or mutating a real destination.

## Why It Matters

This closes the operator loop. DriveDesk is not only detecting a business
problem; it can show exactly how the next internal work item, audit-friendly
event candidate, and safe notification draft would be prepared before anything
is committed.

Verification:

```bash
bash scripts/check_public_business_task_handoff.sh
bash scripts/check_public_demo_api.sh
```

Related docs:

- `docs/public/BUSINESS_TASK_HANDOFF.md` - this contract.
- `docs/public/BUSINESS_INTAKE_PIPELINE.md` - upstream provider signal pipeline.
- `docs/public/WORKFLOW_DEMO.md` - workflow, task, outbox, and proof chain.
- `docs/public/API_BACKED_DEMO.md` - public API and static demo routing.
