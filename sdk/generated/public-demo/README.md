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

GET /demo/business-notification-channels
operationId: business_notification_channels_demo_demo_business_notification_channels_get

GET /demo/business-context-assistant
operationId: business_context_assistant_demo_demo_business_context_assistant_get

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
- `business_notification_channels` manifest entry for
  `GET /demo/business-notification-channels`
- `business_context_assistant` manifest entry for
  `GET /demo/business-context-assistant`
- `DriveDeskPublicDemoClient.getBusinessScenarioReplay`
- `DriveDeskPublicDemoClient.get_business_scenario_replay`

These helpers turn the public `adapterScenarios` payload into a typed
contract-only request/response plan for mapping preview, execution, retry, and
operator-review flows. They do not mutate the public demo.

Connector fixture replay helpers validate the public-safe replay evidence as a
standalone API contract: fixture groups, redaction outcomes, boundaries, and
review docs.

Business scenario replay helpers validate the Business OS scenario contract:
source systems, normalized facts, recommended actions, automation boundaries,
and replay docs.

Business notification channel metadata validates the public-safe channel matrix:
in-app readiness, draft-only external channels, private secret gates, and no
external delivery.

Business Context Assistant metadata validates the public-safe context surface:
CRM, bank, accounting, and legal-reference facts become safe context cards,
insight rules, and next actions through `businessContextAssistant`.

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
