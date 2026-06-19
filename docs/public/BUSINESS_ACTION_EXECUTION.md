# Business Action Execution

DriveDesk action execution is the boundary between recommended operator work
and actual system changes.

The public contract is intentionally preview-only. It proves how DriveDesk can
turn context and suggested actions into an execution plan with idempotency keys,
preflight checks, dry-run results, approval gates, rollback notes, and explicit
provider-write boundaries.

## Public Contract

- Review document: `BUSINESS_ACTION_EXECUTION.md`;
- `GET /demo/business-action-execution` exposes the standalone synthetic proof;
- `GET /demo/public` exposes the same payload as `businessActionExecution`;
- `POST /tenants/{tenant_id}/business-action-executions/preview` is the private
  preview endpoint for computing the same shape from tenant data;
- `business_action_execution.previewed` is the evidence label for the public
  dry-run contract.

## Execution Flow

1. A context or action-plan layer proposes operator work.
2. DriveDesk normalizes each step into an execution candidate.
3. The preview attaches idempotency keys and safe payload profiles.
4. Preflight checks validate payload, idempotency, approval, and secret
   boundaries.
5. Dry-run results show what would be recorded or queued.
6. Approval gates keep provider writes closed until an operator explicitly
   commits a future private execution path.

## Boundary

The public proof does not call CRM, bank, accounting, Telegram, email, SMS, or
webhook providers. It does not persist execution rows. It does not include raw
provider payloads, personal data, credentials, access tokens, browser token
storage, or copied third-party content.

## Verification

```bash
bash scripts/check_public_business_action_execution.sh
bash scripts/check_public_demo_api.sh
```

The checker validates `businessActionExecution`, the standalone
`GET /demo/business-action-execution` endpoint, the OpenAPI schema, static demo
data, UI bindings, SDK manifest metadata, docs links, export wiring, and
public-release gate coverage.
