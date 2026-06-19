# OpenAPI Drift Evidence

DriveDesk exposes a generated OpenAPI contract at:

```text
docs/openapi.json
```

This file is used by the public demo, generated SDK examples, GitHub Pages
links, and API smoke checks. If the FastAPI application changes but
`docs/openapi.json` is not regenerated, the public repository can appear healthy
while the documented API contract is stale.

The OpenAPI drift check prevents that.

## Contract

The verifier compares three public-safe surfaces:

1. the committed `docs/openapi.json`;
2. the OpenAPI schema generated from the current FastAPI application with
   `app.openapi()`;
3. the generated SDK manifest at
   `sdk/generated/public-demo/openapi-client-manifest.json`.

The committed schema must match the generated schema exactly after canonical
JSON serialization. The generated SDK manifest must point to the same
`docs/openapi.json` source and must expose the same public demo operation
contracts used by the demo API and static Pages surface.

## Evidence

The sanitized evidence snapshot is:

```text
docs/public/evidence/openapi-drift.sanitized.json
```

It records:

- the OpenAPI title and version;
- the path and schema counts;
- the public demo endpoints covered by the drift check;
- SHA-256 prefixes for the OpenAPI contract and SDK manifest;
- the public-safe data boundary.

The evidence does not include private endpoints, hostnames, credentials, raw
logs, request bodies, production data, or customer data.

## Verification

```bash
bash scripts/check_public_openapi_drift.sh
```

The same check is included in:

```bash
bash scripts/ci_smoke_public.sh
bash scripts/public_repo_release_gate.sh
```

## Why It Matters

This gives the public engineering surface a stronger API contract boundary:

- API changes must be reflected in the committed OpenAPI artifact;
- SDK examples must remain tied to the current OpenAPI source;
- static demo health is checked against the same API contract;
- public CI fails if the demo contract drifts away from the application.
