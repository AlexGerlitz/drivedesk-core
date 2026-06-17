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

## Why This Matters

The SDK is not meant to be a full production client yet. It proves a foundation:

- DriveDesk publishes a machine-readable API contract.
- The contract can generate working client code.
- The generated client validates the product-shaped demo payload.
- The public repo can prove this in CI without private infrastructure.

## Human Explanation

This is the integration story in a small form. A reviewer can see that DriveDesk
does not only document endpoints manually. It exposes an OpenAPI contract, uses
that contract to generate client code, and verifies that generated code against
the running API.
