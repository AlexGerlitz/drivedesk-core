# Public Demo Health

DriveDesk Core publishes the public demo as a static GitHub Pages surface and
keeps it tied to CI, OpenAPI, generated SDK artifacts, and public-safe evidence.

This contract records the health loop for that surface:

```text
private source
  -> public export gate
  -> public repository CI
  -> GitHub Pages build
  -> Public Demo Health workflow
  -> static demo HTML, demo-data.js, app.js, SDK, docs, and evidence checks
```

## Evidence

Machine-readable evidence:

```text
docs/public/evidence/public-demo-health.sanitized.json
```

Public surface:

```text
https://alexgerlitz.github.io/drivedesk-core/
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
docs/openapi.json
sdk/generated/public-demo/openapi-client-manifest.json
```

Workflow:

```text
.github/workflows/public-demo-health.yml
workflow_dispatch
schedule
```

Verifier:

```bash
bash scripts/check_public_demo_health.sh
```

## Health Signals

The health contract validates that:

- the public export generates `.github/workflows/public-demo-health.yml`;
- the workflow can be run manually and also has a scheduled cadence;
- the hosted demo HTML references `demo-data.js`, `styles.css`, and `app.js`;
- the static fallback exposes `DRIVEDESK_DEMO_DATA`;
- the demo payload contains `notificationDelivery`, `businessScenarioReplay`,
  `integrationExecution`, and `engineeringProof`;
- the generated SDK manifest exposes the OpenAPI-derived demo operations;
- the public docs and evidence index link the health contract.

## Boundary

The health check is public-safe. It checks static assets, synthetic payload
markers, generated client metadata, and public docs. It does not read private
servers, production logs, credentials, raw provider payloads, customer data, or
private deployment state.
