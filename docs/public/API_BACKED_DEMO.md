# DriveDesk API-Backed Demo

This document describes the public-safe demo data contract for DriveDesk Core.
It uses synthetic data only.

## Goal

The public demo should be reviewable as a static GitHub Pages surface, but it
should also prove a real backend contract.

DriveDesk now exposes:

```text
GET /demo/public
```

The endpoint returns the same product-shaped fake data used by the public demo
shell: tenant, health, metrics, work queue, workflow stages, timeline entries,
workflow scenarios, domain events, members, audit events, outbox events, adapter
contracts, adapter operation scenarios, sync jobs, Integration Health, alert
routing, incident response, recovery evidence, and the `engineeringProof`
contract rendered by the Operations, Incidents, and Proof tabs.

## Runtime Modes

| Mode | Behavior |
| --- | --- |
| Static fallback | GitHub Pages loads `demo-data.js` and works without a backend. |
| API-backed | The demo shell loads JSON from `GET /demo/public` when `?demoApi=...` is provided. |

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
```

Client examples:

```bash
BASE_URL=http://localhost:8080 bash examples/curl/demo-public.sh
BASE_URL=http://localhost:8080 python examples/python/demo_public_client.py
BASE_URL=http://localhost:8080 node examples/js/demo-public-fetch.js
```

Generated SDK smoke:

```bash
bash scripts/check_public_demo_sdk.sh
```

`check_public_demo_api.sh` starts a temporary local API when no
`DRIVEDESK_DEMO_BASE_URL` is provided. It checks `/health`, `/ready`,
`/demo/public`, `/openapi.json`, the generated `docs/openapi.json` when
present, alert routes, alert-to-runbook bindings, and then runs the curl,
Python, and JavaScript examples against the same API.

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
operation lifecycle as mapping preview -> execute -> retry -> operator review,
using the same operation contracts documented in
`INTEGRATION_OPERATION_CONTRACTS.md`.

The generated SDK is documented in `CLIENT_SDK.md`. It demonstrates that the
exported OpenAPI schema can produce working Python, JavaScript, and TypeScript
client artifacts.

## Safety Boundary

The endpoint is read-only and fake-data only:

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
response, adapter operation scenarios, recovery evidence, and engineering proof
gates.
