# Generated Public Demo SDK

This folder is generated from `docs/openapi.json` by:

```bash
python scripts/generate_public_demo_sdk.py --openapi docs/openapi.json --out sdk/generated/public-demo
```

Generated clients:

- `python/drivedesk_public_demo_client.py`
- `javascript/drivedesk-public-demo-client.mjs`
- `typescript/drivedesk-public-demo-client.d.ts`

The clients target:

```text
GET /demo/public
operationId: public_demo_demo_public_get

GET /demo/connector-fixture-replay
operationId: connector_fixture_replay_demo_demo_connector_fixture_replay_get

GET /demo/connector-certification
operationId: connector_certification_demo_demo_connector_certification_get

GET /demo/provider-onboarding
operationId: provider_onboarding_demo_demo_provider_onboarding_get

GET /demo/business-notification-channels
operationId: business_notification_channels_demo_demo_business_notification_channels_get

GET /demo/business-context-assistant
operationId: business_context_assistant_demo_demo_business_context_assistant_get

GET /demo/business-action-execution
operationId: business_action_execution_demo_demo_business_action_execution_get

GET /demo/business-approval-gateway
operationId: business_approval_gateway_demo_demo_business_approval_gateway_get

GET /demo/integration-runtime
operationId: integration_runtime_demo_demo_integration_runtime_get

GET /demo/integration-execution
operationId: integration_execution_demo_demo_integration_execution_get

GET /demo/business-scenario-replay
operationId: business_scenario_replay_demo_demo_business_scenario_replay_get
```

Run the SDK smoke:

```bash
bash scripts/check_public_demo_sdk.sh
```

Adapter operation helpers:

- `getAdapterScenario` / `get_adapter_scenario`
- `buildAdapterOperationPlan` / `build_adapter_operation_plan`
- `DriveDeskPublicDemoClient.getAdapterOperationPlan`
- `DriveDeskPublicDemoClient.get_adapter_operation_plan`
- `DriveDeskPublicDemoClient.getConnectorFixtureReplay`
- `DriveDeskPublicDemoClient.get_connector_fixture_replay`
- `DriveDeskPublicDemoClient.getConnectorCertification`
- `DriveDeskPublicDemoClient.get_connector_certification`
- `connector_certification` manifest entry for
  `GET /demo/connector-certification`
- `DriveDeskPublicDemoClient.getProviderOnboarding`
- `DriveDeskPublicDemoClient.get_provider_onboarding`
- `provider_onboarding` manifest entry for
  `GET /demo/provider-onboarding`
- `business_notification_channels` manifest entry for
  `GET /demo/business-notification-channels`
- `business_context_assistant` manifest entry for
  `GET /demo/business-context-assistant`
- `business_action_execution` manifest entry for
  `GET /demo/business-action-execution`
- `business_approval_gateway` manifest entry for
  `GET /demo/business-approval-gateway`
- `integration_runtime` manifest entry for
  `GET /demo/integration-runtime`
- `integration_execution` manifest entry for
  `GET /demo/integration-execution`
- `DriveDeskPublicDemoClient.getBusinessScenarioReplay`
- `DriveDeskPublicDemoClient.get_business_scenario_replay`

These helpers turn the public `adapterScenarios` payload into a typed
contract-only request/response plan for mapping preview, execution, retry, and
operator-review flows. They do not mutate the public demo.

Connector fixture replay helpers validate the public-safe replay evidence as a
standalone API contract: fixture groups, redaction outcomes, boundaries, and
review docs.

Connector certification helpers validate the public-safe provider-readiness
workbench: provider profiles, certification stages, gates, implementation path,
data boundaries, and review docs.

Provider onboarding helpers validate the sandbox-to-private rollout path:
connection profile, mapping preview, preflight checks, sandbox contract, rollout
plan, and provider data boundaries.

Business scenario replay helpers validate the Business OS scenario contract:
source systems, normalized facts, recommended actions, automation boundaries,
and replay docs.

Business notification channel metadata validates the public-safe channel matrix:
in-app readiness, draft-only external channels, private secret gates, and no
external delivery.

Business Context Assistant metadata validates the public-safe context surface:
CRM, bank, accounting, and legal-reference facts become safe context cards,
insight rules, and next actions through `businessContextAssistant`.

Business action execution metadata validates the public-safe execution preview:
idempotency keys, preflight checks, dry-run results, approval gates, rollback
notes, and explicit no-provider-write boundaries.

Business approval gateway metadata validates the public-safe approval preview:
approval requests, RBAC and dual-control checks, approver routing, blocked
commit unlocks, and explicit no-provider-write boundaries.

Integration runtime metadata validates the public-safe adapter runtime:
operation contract selection, scope and idempotency preflight, outbox handoff,
worker boundary, reconciliation planning, incident routing, and no provider
calls in the public demo.

Integration execution metadata validates the public-safe execution timeline:
run ledger, outbox enqueue, worker dispatch, blocked provider call, retry,
dead-letter, reconciliation, observability, and no raw provider payloads.

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
