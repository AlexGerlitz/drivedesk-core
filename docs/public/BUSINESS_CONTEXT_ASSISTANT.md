# Business Context Assistant

DriveDesk treats external systems as context providers. The Business Context
Assistant turns safe CRM, bank, accounting, and legal-reference facts into
operator-ready context inside one work surface.

Public demo contract:

- `GET /demo/business-context-assistant` exposes the standalone synthetic proof;
- `GET /demo/public` exposes the same payload as `businessContextAssistant`;
- `POST /tenants/{tenant_id}/business-workbench-context/preview` is the private
  API shape for role-specific workbench context.

## What It Proves

The assistant shows how DriveDesk can support a user while they work:

- CRM stage says a deal is waiting for payment confirmation;
- bank evidence has a safe amount bucket, not raw payer data;
- accounting export is still pending;
- legal/reference context links the operator to a template or policy reference
  without copying external legal content.

The result is not just a dashboard. It is a next-action surface:

- open reconciliation plan;
- queue accounting export after review;
- attach a policy reference;
- prepare an internal notification draft.

## Public Boundary

The public contract is intentionally read-only:

- no external provider call;
- no provider mutation;
- no credentials;
- no browser token storage;
- no raw provider payload;
- no personal data;
- no copied legal-reference full text.

The public payload carries only safe facts, status labels, action references,
evidence labels, and documentation links.

## Verification

Run:

```bash
bash scripts/check_public_business_context_assistant.sh
```

The checker validates `businessContextAssistant`, the standalone
`GET /demo/business-context-assistant` endpoint, the OpenAPI schema, the static
demo fallback, the UI section, the generated SDK manifest, export wiring, and
the public documentation cross-links.
