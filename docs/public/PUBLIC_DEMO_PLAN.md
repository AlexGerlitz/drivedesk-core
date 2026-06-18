# DriveDesk Public Demo Plan

The public demo should make DriveDesk understandable without using the private
staging runtime.

## Demo Goals

- show the product direction;
- show API and workflow behavior with synthetic demo data;
- show operations behavior with alert routing, escalation, incident response,
  and runbook links;
- show engineering quality through CI, docs, tests, and architecture;
- keep a public demo health workflow for the hosted surface;
- keep operational tooling separate from the public demo.

## Demo Surface

Recommended first public demo:

- a small hosted web shell or static frontend;
- a read-only synthetic FastAPI demo endpoint;
- synthetic tenant and users;
- read-only workflow state with timeline and domain events;
- public OpenAPI docs generated from the demo API;
- public-safe Operations tab with alert routing and runbook bindings;
- public-safe Incidents tab with runbook-backed recovery evidence;
- generated client SDK example from the OpenAPI contract;
- public demo screenshot in the repository README;
- link to the public repository and case study.

## Demo Data

Use synthetic data only:

- sample tenants;
- sample users;
- sample memberships;
- sample audit events;
- sample outbox events;
- sample adapter contracts;
- sample sync jobs with retry and dead-letter states;
- sample workflow stages;
- sample timeline events;
- sample domain events;
- sample alert routes;
- sample alert-to-runbook bindings;
- sample incident response timeline;
- sample recovery actions and resolution evidence;
- sample driving-school domain objects later.

## Verification Flow

The public path should make it possible to:

1. Read the public case study.
2. Inspect architecture diagrams.
3. Inspect `docs/openapi.json` for the API contract.
4. Run the public repo locally.
5. Open `https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/`.
6. See synthetic operational workflows.
7. Inspect the workflow tab for the synthetic lead-to-student flow.
8. Inspect the integration adapter tab.
9. Inspect the Operations tab for alert routes and runbook bindings.
10. Inspect the Incidents tab for runbook-backed recovery evidence.
11. Inspect `GET /demo/public` in `docs/openapi.json`.
12. Run `bash scripts/check_public_demo_api.sh`.
13. Run `bash scripts/check_public_demo_sdk.sh`.
14. Run the curl, Python, or JavaScript demo client example.
15. Read sanitized evidence that staging checks, metrics, logs, and alerts exist.

## Runtime Boundary

The public demo is a product-verification surface. The private staging runtime remains
the engineering surface for deploy, observability, and alerting practice.

The public demo does not need direct access to Prometheus, Grafana, Loki,
Alertmanager, SSH, production backups, or private GitHub Actions secrets.

## Implemented Public Slice

1. Generate OpenAPI schema from the FastAPI app during public export.
2. Add public demo seed data.
3. Build a read-only admin shell.
4. Add tests and public export checks for the shell.
5. Publish the static shell through GitHub Pages.
6. Add a public health endpoint and public CI badge.
7. Link the hosted demo from the public README.
8. Show adapter contracts and sync job states in the public demo shell.
9. Add `GET /demo/public` as a read-only synthetic API payload.
10. Let the static demo load API-backed data through `?demoApi=...` while
    keeping GitHub Pages on static fallback.
11. Add a one-command local API run script.
12. Add a public demo API smoke script that validates the endpoint, OpenAPI, and
    client examples.
13. Add curl, Python, and JavaScript demo clients for `GET /demo/public`.
14. Add a public-safe synthetic workflow with stages, timeline, domain events,
    audit events, and outbox handoff.
15. Add generated OpenAPI client SDK artifacts and SDK smoke checks.
16. Add a public-safe Operations tab backed by the `alertRouting` demo payload.
17. Add a public-safe Incidents tab backed by the `incidentResponse` demo
    payload.
