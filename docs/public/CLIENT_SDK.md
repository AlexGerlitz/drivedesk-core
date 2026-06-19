# DriveDesk Generated Client SDK

This document explains the public-safe generated client SDK example for
DriveDesk Core.

The SDK is generated from the exported OpenAPI schema:

```text
docs/openapi.json
```

It targets the read-only synthetic public demo endpoint:

```text
GET /demo/public
```

## Generated Files

The generated package lives in:

```text
sdk/generated/public-demo/
```

It contains:

- `python/drivedesk_public_demo_client.py`
- `javascript/drivedesk-public-demo-client.mjs`
- `typescript/drivedesk-public-demo-client.d.ts`
- `openapi-client-manifest.json`
- `README.md`

The adapter developer path that uses these generated operation plans is
documented in `ADAPTER_DEVELOPER_GUIDE.md`.

Runnable SDK-backed examples:

- `examples/python/demo_adapter_operation_plan.py`
- `examples/js/demo-adapter-operation-plan.mjs`

## How It Is Generated

The generator is:

```text
scripts/generate_public_demo_sdk.py
```

It reads the OpenAPI schema, finds `GET /demo/public`, extracts the operation
id and required response fields, and writes small public-safe clients.

The SDK smoke is:

```text
scripts/check_public_demo_sdk.sh
```

That smoke does three things:

1. Regenerates the SDK into a temporary directory.
2. Compares the temporary output with the committed generated SDK.
3. Runs the generated Python and JavaScript clients against the local demo API.
4. Runs the adapter operation plan examples against the same local demo API.

## Adapter Operation Helpers

The SDK includes typed helpers around `adapterScenarios`:

- `get_adapter_scenario` / `getAdapterScenario`;
- `build_adapter_operation_plan` / `buildAdapterOperationPlan`;
- `DriveDeskPublicDemoClient.get_adapter_operation_plan`;
- `DriveDeskPublicDemoClient.getAdapterOperationPlan`.

These helpers convert public synthetic adapter scenarios into a
contract-only request/response plan:

```text
adapter scenario -> method/path/headers/body -> expected outputs/evidence
```

Covered public-safe adapter families:

- file import preview and execute;
- Bitrix-style CRM deal preview and ingest;
- worker-backed async execution plans.

Covered phases:

- `preview` - validates mapping and dry-run input shape;
- `execute` - confirms an import/export operation with idempotency key;
- `retry` - describes bounded retry of a failed adapter job;
- `operator_review` - describes dead-letter review without mutation.

CRM ingest scenarios can produce a `WORKER` endpoint such as
`worker:drivedesk_worker.main.process_pending_outbox`, which tells an
integration developer the public SDK is describing a server-side outbox worker
operation, not a browser-callable external write.

The plan has `executionMode: contract_only` and
`safeToRunAgainstPublicDemo: false`. That is intentional: the public endpoint is
read-only, while the SDK still shows the integration contract a real adapter
would follow.

The public payload also exposes `adapterStudio`, which connects the generated
operation plan to the runtime catalog, safe provider-intake preview,
worker-backed outbox ingest, diagnostics, reconciliation, incident cards, and
operator review evidence. The generated clients validate that this workbench
contract is present.

## Why This Matters

The SDK is not meant to be a full production client yet. It proves a foundation:

- DriveDesk publishes a machine-readable API contract.
- The contract can generate working client code.
- The generated client validates the product-shaped demo payload.
- The generated client can build typed adapter operation plans.
- The generated client validates the Adapter Studio workbench contract.
- The generated client can show the Bitrix-style CRM provider-intake body and
  worker-backed ingest operation without exposing real credentials.
- The generated client validates the `engineeringProof` gate shape.
- The public repo can prove this in CI without private infrastructure.

## Engineering Summary

This is the integration surface in a small form. DriveDesk does not only
document endpoints manually. It exposes an OpenAPI contract, uses that contract
to generate client code, verifies that generated code against the running API,
and provides contract-only adapter operation helpers for integration developers.
