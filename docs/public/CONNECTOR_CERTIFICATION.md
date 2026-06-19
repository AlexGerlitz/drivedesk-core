# Connector Certification Path

This document defines the public-safe path for turning any external provider
into a DriveDesk connector.

It sits between `PROVIDER_CONNECTOR_GUIDE.md` and
`ADAPTER_DEVELOPER_GUIDE.md`:

```text
provider idea
  -> provider profile
  -> capability manifest
  -> contract fixtures
  -> local certification gate
  -> runtime readiness review
  -> release proof
  -> private connector implementation
```

The path is provider-neutral. It applies to CRM, bank, accounting, ERP, KKT,
file import, email, telephony, webhook, and custom API connectors.

The public version uses synthetic fixtures and sanitized evidence only. It does
not include real provider secrets, tenant endpoints, raw provider payloads,
customer data, browser tokens, or live external calls.

## Goal

DriveDesk should be able to connect to many systems without creating one-off
integration code for every provider.

The certification path answers six questions before a connector becomes real:

| Question | Required artifact |
| --- | --- |
| What kind of provider is this? | Provider profile |
| What can the connector do? | Capability manifest |
| What payloads must it handle? | Contract fixtures |
| Can it pass local public-safe checks? | Certification gate |
| Is it safe to run privately? | Runtime readiness review |
| Can the public surface prove the shape without secrets? | Release proof |

## Certification Stages

| Stage | Output | Pass signal |
| --- | --- | --- |
| `provider_profile` | Provider class, protocol, direction, auth mode, data classes, rate-limit model, and failure modes. | The provider can be described without secrets or real tenant identifiers. |
| `capability_manifest` | Operations, scopes, idempotency keys, retry policy, dead-letter policy, diagnostics, and reconciliation hooks. | Every operation maps to `operation_contracts` from `GET /integration-adapters`. |
| `contract_fixtures` | Synthetic request, response, failure, redaction, and invalid-payload examples. | Fixture replay proves normalization, redaction, and validation behavior. |
| `local_certification_gate` | Public-safe checker command and evidence JSON. | `bash scripts/check_public_connector_certification.sh` passes. |
| `runtime_readiness_review` | Auth boundary, secret placement, outbox route, worker route, observability, runbook, and incident mapping. | The connector can run server-side without browser token storage. |
| `release_proof` | Public docs, evidence index entry, export manifest, public CI, and release gate coverage. | Public export proves the connector shape without provider credentials. |

## Provider Profile

A provider profile describes the external system before code is written.

Example:

```json
{
  "provider_key": "crm.demo.mock",
  "provider_class": "crm",
  "protocols": ["rest_api", "webhook"],
  "directions": ["inbound"],
  "auth_mode": "oauth2_or_webhook_boundary",
  "credential_placement": "server_secret_store",
  "data_classes": ["business_fact", "pseudonymous_reference"],
  "public_demo_mode": "synthetic_only",
  "rate_limit_model": "provider_backoff",
  "failure_modes": ["timeout", "rate_limited", "validation_error"]
}
```

The profile is safe to publish because it contains shape, not credentials.

Required credential boundary tokens for real providers:

```text
server_secret_store
private_connector_only
no_browser_token_storage
```

## Capability Manifest

The capability manifest describes what DriveDesk can do through the connector.

Example:

```json
{
  "adapter_key": "crm.demo.mock",
  "operations": [
    {
      "key": "crm_deal_intake_preview",
      "phase": "preview",
      "scope": "crm:deal.preview",
      "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "execution_mode": "contract_only",
      "retryable": false,
      "dead_letter": false,
      "operator_review": false
    },
    {
      "key": "crm_deal_ingest_execute",
      "phase": "execute",
      "scope": "crm:deal.ingest",
      "endpoint": "WORKER worker:drivedesk_worker.main.process_pending_outbox",
      "event_type": "integration.crm_deal.ingest.requested",
      "idempotency_keys": ["tenant_id", "batch_id", "deals_hash"],
      "retryable": true,
      "dead_letter": true,
      "operator_review": true
    }
  ]
}
```

This keeps UI, SDK, worker, and runbook behavior aligned around the same
operation shape.

## Contract Fixtures

Fixtures prove behavior before a real provider call exists.

Required fixture groups:

| Fixture group | Purpose |
| --- | --- |
| `happy_path_preview` | Normalizes a safe provider payload into DriveDesk fields. |
| `sensitive_payload_redaction` | Drops tokens, names, phones, emails, addresses, and raw request bodies. |
| `invalid_payload` | Shows validation errors without creating outbox work. |
| `retryable_provider_failure` | Classifies temporary failures for retry. |
| `dead_letter_provider_failure` | Creates operator review for non-retryable or exhausted work. |
| `reconciliation_mismatch` | Shows how provider evidence differs from DriveDesk evidence. |

The public fixture result must prove these flags:

```text
raw_payload_returned=false
credentials_returned=false
external_call_made=false
public_demo_persistence=false
safe_payload_present=true
redaction_evidence_present=true
```

## Certification State Machine

```text
proposed
  -> profile_ready
  -> manifest_ready
  -> fixtures_ready
  -> public_gate_passed
  -> private_connector_ready
  -> production_review_required
```

State meanings:

| State | Meaning |
| --- | --- |
| `proposed` | The provider class and business use case are known. |
| `profile_ready` | The provider profile has protocol, auth, data, rate-limit, and failure-mode shape. |
| `manifest_ready` | Operations map to scopes, idempotency keys, outbox, diagnostics, and recovery. |
| `fixtures_ready` | Synthetic payloads prove normalization, validation, redaction, retry, dead-letter, and reconciliation behavior. |
| `public_gate_passed` | Public docs, evidence JSON, check script, export, smoke, and release gate pass. |
| `private_connector_ready` | Private connector code may add provider client, token exchange, and server-side calls. |
| `production_review_required` | Real provider rollout needs private staging evidence, operator approval, and provider-specific limits. |

## Runtime Readiness Review

A connector is runtime-ready only when it is wired to these DriveDesk surfaces:

| Surface | Required behavior |
| --- | --- |
| `auth_profile` | Describes credential boundary without returning secrets. |
| `server_secret_store` | Keeps provider credentials outside browser and public exports. |
| `operation_contracts` | Describes preview, execute, retry, and review behavior. |
| `outbox` | Executes mutations asynchronously with idempotency. |
| `worker` | Performs provider calls server-side. |
| `drivedesk_integration_connection_checks` | Records safe connection diagnostics. |
| `drivedesk_integration_reconciliations` | Records provider-vs-DriveDesk evidence comparison. |
| `drivedesk_integration_incidents` | Creates incident cards for failed or risky work. |
| `integration.operator_review.created` | Routes dead-letter or risky jobs to review. |
| `EVIDENCE_INDEX.md` | Keeps the public proof discoverable. |

## Connector Classes

| Class | Example provider | First DriveDesk operation |
| --- | --- | --- |
| CRM | Bitrix24-style CRM | `crm_deal_intake_preview` |
| Bank | Bank statement export | `business-provider-intake/preview` |
| Accounting or ERP | 1C-style accounting export | `accounting_export_execute` |
| KKT or receipt provider | Online cash register | outbound document export |
| File import | CSV/XLSX/XML upload | `file_import_preview` |
| Webhook | Custom source event | provider intake preview |
| Email parser | Mailbox attachment import | file import preview |
| Telephony | Call event provider | provider intake preview |
| Custom API | Partner system | adapter-specific preview and execute contract |

## Public Verification

```bash
bash scripts/check_public_connector_certification.sh
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_adapter_developer_guide.sh
bash scripts/check_public_evidence_index.sh
bash scripts/public_repo_release_gate.sh
```

The connector certification check validates:

- this document;
- the machine-readable sanitized evidence snapshot;
- links from Provider Connector Guide, Adapter Developer Guide, Adapter Catalog,
  Operation Contracts, Platform Tour, Project Status, Technical Capability Map,
  Roadmap, README, and Evidence Index;
- private and public smoke path coverage;
- public export manifest coverage;
- release gate coverage.

## Private Implementation Later

After public certification passes, a private connector may add:

- provider HTTP client;
- OAuth, webhook, API key, or mutual-TLS setup;
- token refresh and rotation;
- provider-specific rate-limit handling;
- provider-specific retry classification;
- private staging smoke with synthetic tenant data;
- sanitized evidence export back into the public surface.

The public contract stays stable while the private implementation becomes real.
