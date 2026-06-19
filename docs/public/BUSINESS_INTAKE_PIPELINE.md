# Business Intake Pipeline

DriveDesk can preview a complete intake path for external business signals:

```text
provider event -> safe payload -> role workbench -> detection -> action plan -> notification draft
```

The public contract is exposed in two places:

- `GET /demo/public` as `businessIntakePipeline`;
- `GET /demo/business-intake-pipeline` as a standalone public demo payload;
- `POST /tenants/{tenant_id}/business-intake-pipeline/preview` as the tenant API preview.

The preview is intentionally read-only. It does not call provider APIs, persist
observations, create exceptions, enqueue outbox jobs, send notifications, or
write to external systems.

## Current Synthetic Path

The public demo uses three synthetic provider events:

| Source | State | Purpose |
| --- | --- | --- |
| `crm.bitrix24.mock` | `invoice_sent` | CRM deal still waits for payment. |
| `bank.statement.mock` | `paid` | Bank evidence says money arrived. |
| `accounting.export.mock` | `not_exported` | Accounting export is still blocked. |

DriveDesk normalizes those signals, drops unsafe keys, builds accountant-facing
context cards, detects `crm_payment_mismatch`, prepares an approval-gated
`sync_status` repair candidate, and creates draft-only notification output.

## Data Boundary

The pipeline returns only safe facts:

- no raw provider payloads;
- no credentials;
- no phone numbers;
- no names;
- no external fetches;
- no external mutations;
- no notification delivery.

Dropped key names are visible so an operator can see that redaction happened,
but the dropped values are not returned.

## Why It Matters

This is the core Business OS loop: external systems can send facts into
DriveDesk, but daily work still happens inside DriveDesk. The operator sees the
context, the detected risk, the next action, and the approval boundary in one
place.

Verification:

```bash
bash scripts/check_public_business_intake_pipeline.sh
bash scripts/check_public_demo_api.sh
```

Related docs:

- `docs/public/BUSINESS_INTAKE_PIPELINE.md` - this contract.
- `docs/public/BUSINESS_CONTROL_TOWER.md` - adjacent role workbench previews.
- `docs/public/API_BACKED_DEMO.md` - public API and static demo routing.
