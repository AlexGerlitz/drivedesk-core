# Business Approval Gateway

DriveDesk approval gateway is the control boundary between a dry-run execution
candidate and any future provider-changing commit.

The public contract is intentionally preview-only. It proves how DriveDesk can
turn an action execution candidate into approval requests, policy checks,
approver routing, commit unlock candidates, audit trail entries, and explicit
provider-write boundaries without calling external systems.

## Public Contract

- Review document: `BUSINESS_APPROVAL_GATEWAY.md`;
- `GET /demo/business-approval-gateway` exposes the standalone synthetic proof;
- `GET /demo/public` exposes the same payload as `businessApprovalGateway`;
- `POST /tenants/{tenant_id}/business-approval-gateway/preview` is the private
  preview endpoint for computing the same shape from tenant data;
- `business_approval_gateway.previewed` is the evidence label for the public
  approval contract.

## Approval Flow

1. Action execution produces idempotent dry-run candidates.
2. Provider-changing candidates are converted into approval requests.
3. RBAC, dual-control, idempotency, and provider-write-lock checks run before
   any commit unlock can be considered.
4. Approver routing assigns the review queue, owner role, SLA, and escalation
   path.
5. Commit unlock candidates remain `blocked_until_approved`.
6. Audit trail entries describe what would be recorded when approval is
   requested, checked, and later granted.

## Boundary

The public proof does not approve actions, persist approval rows, unlock
provider writes, call CRM, bank, accounting, Telegram, email, SMS, or webhook
providers, or include raw payloads, personal data, credentials, access tokens,
browser token storage, or copied third-party content.

## Verification

```bash
bash scripts/check_public_business_approval_gateway.sh
bash scripts/check_public_demo_api.sh
```

The checker validates `businessApprovalGateway`, the standalone
`GET /demo/business-approval-gateway` endpoint, the OpenAPI schema, static demo
data, UI bindings, SDK manifest metadata, docs links, export wiring, and
public-release gate coverage.
