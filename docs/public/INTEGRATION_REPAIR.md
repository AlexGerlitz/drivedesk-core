# Integration Repair Workbench

DriveDesk treats integration failures as operational work, not just log lines.
The Integration Repair Workbench shows how retry queues, dead letters, and
reconciliation mismatches become runbook-backed repair work with impact,
ownership, safe actions, approval gates, and post-repair evidence.

Public endpoint:

```http
GET /demo/integration-repair
POST /tenants/{tenant_id}/integration-repairs/preview
```

Public demo field:

```text
integrationRepair
```

## What It Proves

- failed provider work is classified by source type and status;
- each failure is attached to an integration runbook;
- operator impact is visible before a repair action is selected;
- safe diagnostics are separated from retry, mapping repair, and provider work;
- retry and provider-changing actions remain locked behind approval;
- public evidence never includes raw provider payloads, credentials, PII, or
  real provider calls.

## Contract Shape

`integrationRepair.summary`
: High-level counters for incidents, critical items, safe actions, and provider
  writes.

`integrationRepair.incidentMatrix`
: Synthetic retry, dead-letter, and reconciliation incidents with adapter,
  operation, severity, impact, attempts, safe payload summary, and evidence.

`integrationRepair.repairRunbooks`
: Runbook binding for each incident, including alert name, evidence fields, and
  recommended actions.

`integrationRepair.impactAnalysis`
: Business areas affected by integration failure: workflow delivery, financial
  reconciliation, and operator queue.

`integrationRepair.repairActions`
: Candidate actions such as diagnostics, retry after diagnostics, mapping
  profile repair, and reconciliation review. Each action declares approval,
  auto-run, provider-call, mutation, rollback, and evidence fields.

`integrationRepair.safeExecutionPlan`
: Ordered repair flow: classify failure, attach impact, prepare safe actions,
  enforce dry-run, require approval before commit, and observe after repair.

`integrationRepair.dataBoundaries`
: Public-safe boundaries for preview-only repair, safe payload summaries,
  approval before retry, and the private provider runtime.

## Repair Action Preview

The tenant-scoped preview endpoint prepares one safe repair action from the
workbench without persisting a repair action, retrying an outbox event, updating
mapping, or calling a provider.

Example request:

```json
{
  "incident_id": "IR-001",
  "action": "run_connection_diagnostics",
  "operator_role": "operator",
  "include_postchecks": true
}
```

Example response fields:

`selected_incident`
: The incident from the workbench.

`selected_action`
: The requested action if it is valid for the incident.

`preflight_checks`
: Checks proving the incident is known, the action matches the incident, raw
  payload is not required, and provider calls are blocked.

`approval_gate`
: Whether the action is locked behind approval before any private commit.

`dry_run_result`
: What DriveDesk would prepare: diagnostics, retry candidate, mapping repair,
  or reconciliation review.

`postchecks`
: Planned incident, reconciliation, and operator-evidence checks after private
  runtime completes an approved repair.

## Public-Safe Rule

The workbench does not execute a retry, mutate a provider, fetch a real provider
payload, or expose a secret. It only proves the repair contract that private
runtime code must satisfy.

Required flags:

```text
providerCallEnabled=false
externalMutation=false
rawPayloadIncluded=false
containsPii=false
```

## Private Runtime Path

The private implementation can use this same contract to:

1. read failed outbox and reconciliation records;
2. select a runbook from status and source type;
3. show business impact and safe payload summary;
4. run diagnostics first;
5. require approval before retry or provider-changing work;
6. execute idempotent repair work through the outbox;
7. refresh reconciliation, metrics, and incident evidence.

## Verification

```bash
bash scripts/check_public_integration_repair.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
```
