# Provider Connector Guide

This guide describes the public-safe provider connector path for DriveDesk.
It is written for future authenticated adapters without exposing real secrets,
tenant endpoints, customer data, or provider payloads.

## Goal

External systems should not become the DriveDesk operating center. They feed or
receive business facts through connector contracts.

The connector path is:

```text
provider payload or export request
  -> runtime adapter catalog
  -> tenant-owned connection profile
  -> mapping preview
  -> provider intake or export operation
  -> outbox-backed execution
  -> diagnostics, reconciliation, incident, and operator review evidence
  -> business workbench context and action planning
```

## Provider Classes

| Provider class | Public-safe runtime shape | Main contract | Evidence |
| --- | --- | --- | --- |
| Bitrix24-style CRM | `crm.bitrix24.mock` | CRM deal facts become safe provider intake observations. | `business_provider_intake.previewed`, `integration.crm_deal.ingest.requested` |
| Bank statements | future bank adapter using the same intake boundary | Payment facts become normalized observations for reconciliation. | `business_state.observation.recorded`, `drivedesk_business_exceptions` |
| Accounting and ERP | `accounting.export.mock` | DriveDesk exports safe document summaries through an outbound adapter. | `accounting.export.requested`, `drivedesk_integration_reconciliations` |
| File import | `file.import.fake` | Uploaded rows are mapped, previewed, and executed through the outbox. | `integration.mapping_preview.completed`, `integration.file_import.requested` |

## Auth Boundary

Every provider connector starts with the adapter catalog:

```text
GET /integration-adapters
```

The catalog returns `auth_profile`. This is not a secret. It is the public-safe
description of how a future real connector handles credentials.

For Bitrix24-style CRM:

```json
{
  "adapter_key": "crm.bitrix24.mock",
  "auth_profile": {
    "mode": "oauth2_or_webhook_boundary",
    "public_demo_requires_secret": false,
    "real_provider_requires_secret": true,
    "secret_refs": ["BITRIX24_WEBHOOK_URL", "BITRIX24_CLIENT_SECRET"],
    "credential_placement": "server_secret_store",
    "token_exchange": "private_connector_only",
    "data_boundaries": [
      "no_public_secrets",
      "no_browser_token_storage",
      "server_side_provider_calls_only"
    ]
  }
}
```

This lets the public project explain the real-provider shape without putting a
webhook URL, OAuth client secret, access token, refresh token, tenant domain, or
raw provider response in GitHub Pages or JavaScript.

## Connection Profile

A tenant-owned connection profile binds an adapter to a tenant, scopes, and
field mapping.

```json
{
  "adapter_key": "crm.bitrix24.mock",
  "display_name": "Bitrix24 CRM Deal Intake",
  "scopes": ["crm:deal.preview", "crm:deal.ingest"],
  "mapping": {
    "deal_id": "ID",
    "source_state": "STAGE_ID",
    "owner_role": "ASSIGNED_BY_ROLE",
    "amount": "OPPORTUNITY"
  }
}
```

The mapping points from DriveDesk-owned fields to provider-shaped field names.
The public contract stores mapping keys and examples only; it does not store
real payload values.

## Preview Before Execution

Preview endpoints let an operator validate provider data before persistence or
external writes.

```text
POST /tenants/{tenant_id}/integration-mapping-preview
POST /tenants/{tenant_id}/business-provider-intake/preview
POST /tenants/{tenant_id}/business-workbench-context/preview
```

The preview result should show:

- normalized DriveDesk fields;
- safe payload subsets such as amount bucket, source state, and owner role;
- dropped sensitive key names;
- whether raw payload, PII, provider credentials, external fetches, or external
  writes were included;
- the next safe DriveDesk steps.

## Execute Through Outbox

Execution is asynchronous and auditable:

```text
POST /tenants/{tenant_id}/business-provider-intake/preview
  -> operator or workflow chooses ingest
  -> integration.crm_deal.ingest.requested
  -> outbox
  -> worker
  -> adapter
  -> reconciliation, incident, or operator review if needed
```

The same pattern is used for outbound accounting export:

```text
POST /tenants/{tenant_id}/integration-exports/accounting
  -> accounting.export.requested
  -> outbox
  -> worker
  -> accounting.export.mock
```

## Observability And Recovery

Connectors are observable through existing public-safe surfaces:

| Surface | Purpose |
| --- | --- |
| `drivedesk_integration_connection_checks` | Connection diagnostics without raw provider payloads. |
| `drivedesk_integration_reconciliations` | Provider evidence comparison and mismatch tracking. |
| `drivedesk_integration_incidents` | Incident cards for retry, dead-letter, and reconciliation states. |
| `integration.operator_review.created` | Manual review queue for failed or risky connector jobs. |
| `OUTBOX_RECOVERY.md` | Audited operator retry path. |

## Public Demo Proof

The public demo proves the connector shape without real providers:

- `GET /demo/public` returns adapter cards with `authProfile`;
- `adapterScenarios` cover preview, execute, retry, and operator review;
- the Business Control Tower shows CRM provider intake, workbench context,
  detection, action planning, notification preview, and dry-run repair;
- `check_public_demo_api.sh` validates `/demo/public`,
  `/integration-adapters`, operation contracts, and auth boundaries;
- `check_public_provider_connector_guide.sh` validates this guide and public
  navigation.

## Private Implementation Later

When a real connector is added privately, it should reuse the same public
contract:

1. add a private provider client;
2. keep provider secrets in server-side secret storage;
3. keep token exchange in private connector code;
4. map provider payloads into DriveDesk-owned fields;
5. run preview before persistence or writes;
6. execute through outbox;
7. emit diagnostics, reconciliation, incident, and operator-review evidence;
8. expose only sanitized status and aggregate evidence to the public surface.

## Verification

```bash
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_business_control_tower.sh
```
