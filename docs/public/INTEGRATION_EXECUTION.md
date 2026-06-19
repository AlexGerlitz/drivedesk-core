# Integration Execution Timeline

DriveDesk models adapter execution as a reviewed timeline, not as a hidden
provider call. The public demo keeps this contract synthetic and read-only.

## Public Endpoints

```text
GET /demo/integration-execution
POST /tenants/{tenant_id}/integration-executions/preview
```

`GET /demo/integration-execution` returns the public-safe evidence used by the
demo UI. `POST /tenants/{tenant_id}/integration-executions/preview` returns the
same lifecycle shape for a tenant-selected adapter operation without creating
database rows or calling a provider.

## Execution Stages

| Stage | Meaning |
| --- | --- |
| `request_accepted` | The platform accepts an adapter execution request and prepares a run ledger. |
| `runtime_preflight` | Adapter contract, scopes, idempotency, and secret boundaries are checked. |
| `approval_gate` | Provider-changing work stays locked until approval and an idempotent outbox commit. |
| `outbox_enqueue` | The operation is represented as an outbox event instead of an inline provider write. |
| `worker_dispatch` | Worker execution is selected behind the public-safe boundary. |
| `provider_call` | Public demo blocks provider calls and records only contract evidence. |
| `reconciliation` | Expected internal results are linked to later provider evidence. |
| `operator_closure` | Retry, dead-letter, or reconciliation evidence is routed to the operator. |

## What This Proves

- The adapter runtime has a run ledger and idempotency fingerprint.
- The run ledger shows where a real execution would create `WorkflowActionRun`
  and `OutboxEvent` records.
- Provider calls are not made from public demo paths.
- Outbox, worker, `IntegrationReconciliation`, `IntegrationIncident`, and
  metrics are part of one execution lifecycle.
- Failure handling is explicit through retry queue, dead-letter review, and
  reconciliation mismatch routes.
- Raw provider payloads, secrets, and personal data are not returned.

## Verification

```bash
bash scripts/check_public_integration_execution.sh
bash scripts/check_public_demo_api.sh
bash scripts/public_repo_release_gate.sh
```
