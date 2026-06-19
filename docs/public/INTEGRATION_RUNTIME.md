# Integration Runtime

DriveDesk Integration Runtime turns adapter contracts into an execution path that
can be reviewed before any external system is changed.

The runtime preview answers five questions:

- which adapter operation was selected;
- which tenant scope, idempotency keys, and approval dependency apply;
- whether the operation would enter the outbox;
- which worker boundary would execute it;
- how reconciliation, retry, dead-letter, and incident review would be handled.

Public demo endpoints:

```text
GET /demo/integration-runtime
POST /tenants/{tenant_id}/integration-runtime/preview
```

The public demo uses `accounting.export.mock` and
`accounting_export_execute`. It is intentionally contract-only:

- no provider API call is made;
- no outbox event is queued;
- no secret value is returned;
- no raw provider payload or personal data is included;
- provider write remains closed until approval and commit exist.

Runtime stages:

| Stage | Purpose | Evidence |
| --- | --- | --- |
| `contract_selected` | Select the operation from the runtime adapter catalog. | `adapter_runtime.contract_selected` |
| `scope_preflight` | Check the required tenant connection scope. | `adapter_runtime.scope_checked` |
| `idempotency_prepared` | Attach deterministic idempotency keys before enqueue. | `adapter_runtime.idempotency_prepared` |
| `approval_dependency` | Keep provider-changing work behind approval. | `adapter_runtime.approval_dependency_attached` |
| `outbox_handoff` | Prepare the event that would enter the outbox. | `adapter_runtime.outbox_handoff_prepared` |
| `worker_boundary` | Select the async worker execution boundary. | `adapter_runtime.worker_boundary_selected` |
| `reconciliation_plan` | Compare provider evidence after execution. | `adapter_runtime.reconciliation_planned` |

The standalone payload also carries `adapter_runtime.previewed` as the summary
event for the public-safe runtime preview.

This is the adapter execution bridge between the public Integration Hub story and
the private connector implementation. A real Bitrix24, 1C, bank, KKT, webhook,
or accounting connector should reuse this contract shape while keeping provider
credentials and provider payloads in private server-side code.

Verification:

```bash
bash scripts/check_public_integration_runtime.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
```
