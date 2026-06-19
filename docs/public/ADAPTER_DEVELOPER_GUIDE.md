# Adapter Developer Guide

This guide describes how a new DriveDesk provider adapter moves from a public
contract to a private implementation.

It is public-safe on purpose: the steps use synthetic adapter scenarios,
generated SDK operation plans, and documented credential boundaries. Real
provider secrets, raw payloads, tenant data, browser tokens, and production
provider calls are outside this document.

## Goal

The developer path is:

```text
GET /demo/public
  -> adapterScenarios
  -> generated SDK operation plan
  -> adapter descriptor
  -> auth_profile
  -> tenant connection profile
  -> preview endpoint
  -> outbox-backed execute operation
  -> diagnostics, reconciliation, incident, and operator review evidence
```

For a Bitrix24-style CRM connector, the public-safe path is:

```text
adapter-crm-deal-preview
  -> crm_deal_intake_preview
  -> POST /tenants/{tenant_id}/business-provider-intake/preview
  -> safe_payload + normalized_observation + no_provider_call

adapter-crm-deal-ingest
  -> crm_deal_ingest_execute
  -> WORKER worker:drivedesk_worker.main.process_pending_outbox
  -> integration.crm_deal.ingest.requested
  -> retry + dead-letter + operator_review
```

## 1. Start From The Runtime Catalog

Every provider begins in the runtime adapter catalog:

```text
GET /integration-adapters
```

The descriptor must expose:

- `adapter_key`;
- `payload_schema`;
- `required_mapping_keys`;
- `supported_connection_scopes`;
- `default_connection_scopes`;
- `operation_contracts`;
- `auth_profile`;
- public-safe capabilities and failure modes.

The Bitrix24-style public adapter is `crm.bitrix24.mock`. Its real connector
must keep the same operation shape while replacing synthetic provider access
with private server-side provider calls.

## 2. Generate A Contract-Only SDK Plan

The generated SDK exposes:

```text
build_adapter_operation_plan
buildAdapterOperationPlan
DriveDeskPublicDemoClient.get_adapter_operation_plan
DriveDeskPublicDemoClient.getAdapterOperationPlan
```

The public examples prove two adapter plans:

```text
examples/python/demo_adapter_operation_plan.py
examples/js/demo-adapter-operation-plan.mjs
```

Required scenario coverage:

| Scenario | Operation | Endpoint mode | Purpose |
| --- | --- | --- | --- |
| `adapter-file-import-preview` | `file_import_preview` | HTTP POST | Mapping dry run. |
| `adapter-file-import-execute` | `file_import_execute` | HTTP POST | Outbox-backed file import. |
| `adapter-crm-deal-preview` | `crm_deal_intake_preview` | HTTP POST | Bitrix-style provider intake preview. |
| `adapter-crm-deal-ingest` | `crm_deal_ingest_execute` | `WORKER` | Async CRM ingest through the worker. |
| `adapter-accounting-export-retry` | `accounting_export_execute` | HTTP POST | Retryable outbound export. |
| `adapter-dead-letter-review` | `file_import_execute` | HTTP GET | Operator review for dead-letter work. |

The SDK plans use `executionMode: contract_only` and
`safeToRunAgainstPublicDemo: false`. This lets developers see the production
request shape without making public external writes.

## 3. Implement The Preview Boundary First

Preview comes before execution.

For CRM, the SDK operation plan must produce a body shaped like:

```json
{
  "dryRun": true,
  "provider_key": "crm.bitrix24.mock",
  "source_type": "crm_deal",
  "subject_type": "deal",
  "subject_id": "DEAL-2026-001",
  "external_ref": "crm-deal-001",
  "provider_payload": {
    "stage": "invoice_sent",
    "amount": 1500,
    "owner_role": "sales",
    "full_name": "Synthetic Customer",
    "phone": "+70000000000",
    "access_token": "never-return-this"
  }
}
```

Expected public-safe outputs:

- `safe_payload`;
- `normalized_observation`;
- `no_provider_call`;
- dropped sensitive keys such as `access_token`, `full_name`, and `phone`;
- no persistence;
- no external mutation;
- no raw provider payload returned.

This proves the redaction and normalization contract before any private
connector uses a real provider API.

## 4. Implement Execution Through Outbox

Execute operations must not be one-off request handlers. They must use the
same async pattern:

```text
request or workflow action
  -> idempotency key
  -> audit event
  -> outbox event
  -> worker execution
  -> retry or dead-letter
  -> operator_review if needed
```

For CRM ingest, the event is:

```text
integration.crm_deal.ingest.requested
```

The operation contract must include idempotency keys such as:

```text
tenant_id, batch_id, deals_hash
```

The worker endpoint is represented as:

```text
WORKER worker:drivedesk_worker.main.process_pending_outbox
```

That is intentional. A connector developer sees that the operation is not a
browser-callable endpoint and must be processed server-side.

## 5. Keep Credentials Behind The Auth Profile

The `auth_profile` is the contract for secrets and token exchange.

For Bitrix24-style CRM, required boundary tokens are:

```text
oauth2_or_webhook_boundary
server_secret_store
private_connector_only
no_browser_token_storage
server_side_provider_calls_only
```

Rules for real connectors:

- do not store provider tokens in the browser;
- do not return provider tokens in API responses;
- do not write provider credentials into logs, metrics, traces, screenshots, or
  public evidence;
- keep token exchange and refresh logic inside private connector code;
- expose only status, scopes, safe config, diagnostics, and evidence.

## 6. Add Diagnostics, Reconciliation, And Incident Evidence

A provider is not ready when it only returns `200 OK`.

A ready connector must connect to:

- `drivedesk_integration_connection_checks`;
- `drivedesk_integration_reconciliations`;
- `drivedesk_integration_incidents`;
- retry counters;
- dead-letter state;
- operator review cards;
- runbook links.

This keeps failures visible and recoverable.

## 7. Verification

Minimum checks for a public-safe adapter developer change:

```bash
bash scripts/check_public_adapter_developer_guide.sh
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/check_public_demo_api.sh
bash scripts/public_repo_release_gate.sh
```

The SDK check proves:

- the OpenAPI-generated clients are current;
- `adapter-crm-deal-preview` produces a provider-intake request plan;
- `adapter-crm-deal-ingest` is represented as a `WORKER` operation;
- Python and JavaScript examples exercise CRM provider plans;
- public smoke can validate everything without real provider credentials.

## Private Implementation Later

The private connector can then add:

- real Bitrix24 OAuth or webhook configuration;
- server-side token exchange and refresh;
- private provider HTTP client;
- provider rate-limit handling;
- provider-specific retry classification;
- private staging smoke with synthetic tenant data;
- sanitized evidence export back to the public repo.

The public shape stays stable while the private connector becomes real.
