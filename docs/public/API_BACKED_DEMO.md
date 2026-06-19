# DriveDesk API-Backed Demo

This document describes the public-safe demo data contract for DriveDesk Core.
It uses synthetic data only.

## Goal

The public demo should be reviewable as a static GitHub Pages surface, but it
should also prove a real backend contract.

DriveDesk now exposes:

```text
GET /demo/public
GET /demo/connector-fixture-replay
GET /demo/business-intake-pipeline
GET /demo/business-task-handoff
GET /demo/business-notification-channels
GET /demo/business-context-assistant
GET /demo/business-action-execution
GET /demo/business-scenario-replay
```

`GET /demo/public` returns the same product-shaped synthetic demo data used by
the public demo shell: tenant, health, metrics, work queue, workflow stages,
timeline entries, workflow scenarios, domain events, members, audit events,
outbox events, adapter contracts, adapter operation scenarios, Adapter Studio,
sync jobs, Integration Health, alert routing, incident response,
`businessControlTower` data, `businessIntakePipeline`,
`businessTaskHandoff`, `businessNotificationChannels`,
`businessContextAssistant`, `businessActionExecution`,
`businessScenarioReplay`, recovery evidence,
`connectorFixtureReplay`, and the `engineeringProof` contract rendered by the
Control Tower, Integrations, Operations, Incidents, and Proof tabs.

`GET /demo/connector-fixture-replay` returns the same `connectorFixtureReplay`
contract as a standalone endpoint. It is useful when a reviewer wants to inspect
only the integration replay proof: fixture groups, redaction outcomes,
read-only boundaries, evidence paths, and docs.

`GET /demo/business-intake-pipeline` returns the same
`businessIntakePipeline` contract as a standalone endpoint. It is useful for
checking the active preview loop directly: provider event -> safe payload ->
role workbench -> detection -> action plan -> notification draft.

`GET /demo/business-task-handoff` returns the same `businessTaskHandoff`
contract as a standalone endpoint. It is useful for checking the operator
handoff loop directly: action plan -> internal task cards -> internal outbox
candidates -> draft in-app notifications.

`GET /demo/business-notification-channels` returns the same
`businessNotificationChannels` contract as a standalone endpoint. It is useful
for checking the notification readiness loop directly: internal action -> safe
drafts -> channel gates -> no external delivery.

`GET /demo/business-context-assistant` returns the same
`businessContextAssistant` contract as a standalone endpoint. It is useful for
checking the context loop directly:
`POST /tenants/{tenant_id}/business-workbench-context/preview` -> safe CRM,
bank, accounting, and legal-reference facts -> insight rules -> next actions.

`GET /demo/business-action-execution` returns the same
`businessActionExecution` contract as a standalone endpoint. It is useful for
checking the execution-readiness loop directly:
`POST /tenants/{tenant_id}/business-action-executions/preview` -> idempotency
keys -> preflight checks -> dry-run results -> approval gates -> no provider
writes.

The public review page for this contract is
`docs/public/BUSINESS_ACTION_EXECUTION.md`.

`GET /demo/business-scenario-replay` returns the same
`businessScenarioReplay` contract as a standalone endpoint. It is useful for
checking the Business OS loop directly: external signal -> normalized facts ->
risk detection -> role context -> approval-aware action plan.

## Runtime Modes

| Mode | Behavior |
| --- | --- |
| Static fallback | GitHub Pages loads `demo-data.js` and works without a backend. |
| API-backed | The demo shell loads JSON from `GET /demo/public` when `?demoApi=...` is provided. |
| Replay API | The generated SDK and smoke checks can load `GET /demo/connector-fixture-replay` directly. |
| Intake Pipeline API | Smoke checks can load `GET /demo/business-intake-pipeline` directly. |
| Task Handoff API | Smoke checks can load `GET /demo/business-task-handoff` directly. |
| Notification Channel API | Smoke checks can load `GET /demo/business-notification-channels` directly. |
| Business Context Assistant API | Smoke checks can load `GET /demo/business-context-assistant` directly. |
| Business Action Execution API | Smoke checks can load `GET /demo/business-action-execution` directly. |
| Scenario Replay API | Smoke checks can load `GET /demo/business-scenario-replay` directly. |

Example local API-backed run:

```bash
bash scripts/run_public_demo_local.sh
```

Then open the static demo with:

```text
apps/admin/public-demo/index.html?demoApi=http://localhost:8080/demo/public
```

Contract smoke:

```bash
bash scripts/check_public_demo_api.sh
bash scripts/check_public_business_control_tower.sh
```

Client examples:

```bash
BASE_URL=http://localhost:8080 bash examples/curl/demo-public.sh
BASE_URL=http://localhost:8080 python examples/python/demo_public_client.py
BASE_URL=http://localhost:8080 node examples/js/demo-public-fetch.js
BASE_URL=http://localhost:8080 python examples/python/demo_adapter_operation_plan.py
BASE_URL=http://localhost:8080 node examples/js/demo-adapter-operation-plan.mjs
```

Generated SDK smoke:

```bash
bash scripts/check_public_demo_sdk.sh
```

`check_public_demo_api.sh` starts a temporary local API when no
`DRIVEDESK_DEMO_BASE_URL` is provided. It checks `/health`, `/ready`,
`/demo/public`, `/demo/connector-fixture-replay`,
`/demo/business-intake-pipeline`, `/demo/business-task-handoff`,
`/demo/business-notification-channels`, `/demo/business-context-assistant`,
`/demo/business-action-execution`,
`/demo/business-scenario-replay`,
`/openapi.json`, the generated
`docs/openapi.json` when present, alert routes, alert-to-runbook bindings,
connector certification references in `CONNECTOR_CERTIFICATION.md`, connector
fixture replay references in `CONNECTOR_FIXTURE_REPLAY.md`, business scenario
replay references in `BUSINESS_SCENARIO_REPLAY.md`, and then runs the curl,
Python, and JavaScript examples against the same API.

The `connectorFixtureReplay` payload is the API-backed form of
`CONNECTOR_FIXTURE_REPLAY.md`: it exposes the synthetic fixture groups, replay
outcomes, read-only boundaries, and evidence links rendered in the Integrations
tab. The standalone replay endpoint exposes the same contract without requiring
the full public demo payload.

The business control tower payload is documented in
`BUSINESS_CONTROL_TOWER.md`. It shows the synthetic path:

```text
CRM observation + bank observation + accounting observation
  -> business exception
  -> repair action proposal
  -> approval
  -> dry-run repair evidence
```

The `businessIntakePipeline` payload is documented in
`BUSINESS_INTAKE_PIPELINE.md`. It shows the preview-only path from synthetic
CRM, bank, and accounting provider events to safe payloads, accountant
workbench cards, `crm_payment_mismatch` detection, approval-gated repair
planning, and draft-only notifications.

The `businessTaskHandoff` payload is documented in
`BUSINESS_TASK_HANDOFF.md`. It shows the preview-only path from approved action
steps to internal task cards, internal outbox candidates, and draft in-app
notifications without persistence, external provider writes, or external
delivery.

The `businessNotificationChannels` payload is documented in
`BUSINESS_NOTIFICATION_CHANNELS.md`. It shows the preview-only path from
operator action to in-app, Telegram, email, SMS, and webhook readiness,
safe delivery drafts, private secret gates, and no external delivery.

The `businessScenarioReplay` payload is documented in
`BUSINESS_SCENARIO_REPLAY.md`. It shows three reusable Business OS paths:
CRM/bank/accounting mismatch, support SLA risk, and procurement delay risk. The
contract proves that DriveDesk can keep the same normalization, detection,
context, action-plan, and approval boundary across different external systems.

The incident response payload is documented in `INCIDENT_RESPONSE_DEMO.md`. It
shows the synthetic path:

```text
alert -> incident -> owner -> runbook -> mitigation -> recovery evidence
```

The Proof tab contract is documented in `ENGINEERING_PROOF.md` and checked by:

```bash
bash scripts/check_public_engineering_proof.sh
```

The workflow payload is documented in `WORKFLOW_DEMO.md`. It demonstrates the
synthetic path:

```text
lead -> student -> contract -> audit -> outbox -> integration sync
```

It also exposes reusable `workflowScenarios` so the demo can show automation as
trigger -> action type -> outputs -> evidence instead of only a single timeline.

The integration payload includes `adapterScenarios`. These show the adapter
operation lifecycle as mapping preview -> CRM intake preview -> execute ->
retry -> operator review, using the same operation contracts documented in
`INTEGRATION_OPERATION_CONTRACTS.md`.

The same payload now includes `adapterStudio`. This is the public integration
workbench contract: runtime catalog -> generated SDK operation plan -> safe CRM
preview -> worker/outbox ingest -> diagnostics and operator review. It keeps the
public demo read-only while showing the exact boundary a real Bitrix-style
provider connector would follow.

Adapter cards also include `authProfile` metadata from the runtime catalog. The
static fallback and API-backed payload both show whether the public demo needs a
secret, whether a real provider needs one, where credentials must be placed, and
whether browser token storage is forbidden.

The future real-provider path is documented in `PROVIDER_CONNECTOR_GUIDE.md`.
That guide ties `authProfile`, connection scopes, mapping preview, provider
intake, outbox execution, diagnostics, reconciliation, incidents, and operator
review into one connector lifecycle.

The generated SDK is documented in `CLIENT_SDK.md`. It demonstrates that the
exported OpenAPI schema can produce working Python, JavaScript, and TypeScript
client artifacts, including typed adapter operation helpers that turn
`adapterScenarios` into contract-only request/response plans.

## Safety Boundary

The endpoint is read-only and synthetic-data only:

- no production database access is required;
- no private infrastructure details are returned;
- no personal data is returned;
- no credentials or server paths are returned;
- GitHub Pages can still run without an API.

## Engineering Summary

This is the first public frontend/backend contract. The static demo works
without infrastructure, and the same UI can be pointed at the FastAPI endpoint
to verify that the backend owns the demo payload shape: workflow, timeline,
workflow scenarios, domain events, audit, outbox data, alert routing, incident
response, business control tower data, business scenario replay data, adapter
operation scenarios, recovery evidence, Adapter Studio, and engineering proof
gates.
