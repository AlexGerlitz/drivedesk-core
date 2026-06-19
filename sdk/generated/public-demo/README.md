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

These helpers turn the public `adapterScenarios` payload into a typed
contract-only request/response plan for mapping preview, execution, retry, and
operator-review flows. They do not mutate the public demo.

Connector fixture replay helpers validate the public-safe replay evidence as a
standalone API contract: fixture groups, redaction outcomes, boundaries, and
review docs.

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
