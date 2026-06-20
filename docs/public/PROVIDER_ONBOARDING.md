# Provider Onboarding Workbench

DriveDesk treats every external system as a provider that must pass the same
onboarding path before it can affect business data.

The public workbench uses `crm.bitrix24.mock` as the first provider profile. It
does not call Bitrix24, 1C, banks, email, Telegram, or any other real provider.
It shows the production shape of the process with synthetic data only.

## Contract

Public API:

```text
GET /demo/provider-onboarding
```

Public payload:

- `providerProfile` describes adapter identity, auth mode, scopes, operation
  keys, and server-side secret references.
- `onboardingStages` shows the path from provider selection to private rollout.
- `readinessGates` shows what is already ready and what still blocks a real
  private connector rollout.
- `readinessBlockers` lists only the blocking gates that must be cleared before
  write-mode provider execution.
- `privateConnectorHandoff` turns the public-safe sandbox proof into the next
  private implementation checklist.
- `mappingPreview` proves that provider fields can be normalized without raw
  provider payloads.
- `preflightChecks` proves scope, mapping, secret reference, and provider-call
  boundaries.
- `sandboxContract` links the preview operation, execution operation, runtime
  steps, and execution timeline.
- `rolloutPlan` shows what must happen before a private connector can write to a
  provider.
- `dataBoundaries` records what the browser, public demo, server secret store,
  and private provider runtime may see.

## Onboarding Flow

```text
select_provider_profile
  -> bind_connection_profile
  -> mapping_preview
  -> sandbox_dry_run
  -> approval_review
  -> private_rollout
  -> monitor_and_reconcile
```

The workbench links existing DriveDesk surfaces:

- `GET /integration-adapters`
- `POST /tenants/{tenant_id}/integration-mapping-preview`
- `POST /tenants/{tenant_id}/integration-runtime/preview`
- `POST /tenants/{tenant_id}/business-approval-gateway/preview`
- `GET /demo/connector-certification`
- `GET /demo/connector-fixture-replay`
- `GET /demo/integration-execution`

## Why It Exists

Connector certification answers: "is this provider contract complete enough?"

Provider onboarding answers: "how does a tenant actually move from provider
metadata to a reviewed private rollout?"

That matters for a real Business OS because integrations are not just API calls.
They need:

- tenant-scoped connection profiles;
- mapping validation;
- server-side secret references;
- dry-run or sandbox execution;
- approval before writes;
- idempotency;
- retry and dead-letter handling;
- reconciliation;
- observability;
- scheduled validation after rollout.

## Bitrix-Style Provider Path

For the current Bitrix-style CRM provider:

```text
crm.bitrix24.mock
  preview: crm_deal_intake_preview
  execute: crm_deal_ingest_execute
  scopes: crm:deal.preview, crm:deal.ingest
  secrets: BITRIX24_WEBHOOK_URL, BITRIX24_CLIENT_SECRET
```

The public demo exposes the secret reference names only. Secret values belong in
the private server-side secret store.

## Readiness Gates

The onboarding workbench gives the current provider a bounded readiness score:

```text
readinessScore=72
readinessStatus=sandbox_ready_private_blocked
```

This does not mean the real provider is fully live. It means the public-safe
sandbox contract is ready and the private rollout is blocked only by things
that must stay outside the public repository:

- `private_secret_binding` - real webhook URL, OAuth secret, tenant domain, and
  refresh flow must be bound in private secret storage.
- `provider_sandbox_dry_run` - real provider sandbox read/dry-run must prove
  auth, rate limits, pagination, and error mapping.
- `write_unlock_approval` - write mode stays locked until approval,
  idempotency, rollback, and observability evidence are attached.

The handoff contract records the next private milestone:

```text
privateConnectorHandoff.nextMilestone=real_provider_sandbox_dry_run
```

That is the bridge from public portfolio proof to real commercial connector
work.

## Public Safety

The public workbench is safe because:

- `providerCallEnabled=false`;
- `externalMutation=false`;
- `rawPayloadIncluded=false`;
- `containsPii=false`;
- browser output is metadata and evidence only;
- real provider clients stay behind `private_connector_only`.

## Verification

```bash
bash scripts/check_public_provider_onboarding.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/public_repo_release_gate.sh
```

Evidence:

- `docs/public/evidence/provider-onboarding.sanitized.json`
- `docs/public/PROVIDER_CONNECTOR_GUIDE.md`
- `docs/public/CONNECTOR_CERTIFICATION.md`
- `docs/public/CONNECTOR_FIXTURE_REPLAY.md`
- `docs/public/INTEGRATION_RUNTIME.md`
- `docs/public/INTEGRATION_EXECUTION.md`
