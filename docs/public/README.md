# DriveDesk Public Engineering Surface

This folder contains the public-safe engineering surface for DriveDesk. It is
written so an external reviewer can understand the project without access to
private infrastructure, production history, customer data, or operational
credentials.

## Documents

- `PORTFOLIO_CASE_STUDY.md` - engineering case study and current system shape.
- `SYSTEM_DESIGN.md` - public-safe system design overview.
- `API_BACKED_DEMO.md` - read-only synthetic API contract for the public demo.
- `WORKFLOW_DEMO.md` - synthetic business workflow, timeline, events, audit,
  and outbox overview.
- `AUTH_FOUNDATION.md` - credential auth, bearer token, and RBAC overview.
- `CLIENT_SDK.md` - generated OpenAPI client SDK example.
- `INTEGRATION_ADAPTERS.md` - adapter contract, outbox, retry, and dead-letter overview.
- `INTEGRATION_OBSERVABILITY.md` - adapter metrics, worker logs, and failure visibility overview.
- `ARCHITECTURE_DIAGRAMS.md` - public-safe architecture diagrams.
- `PUBLIC_DEMO_PLAN.md` - future live demo plan.
- `ROADMAP.md` - public-safe engineering roadmap.
- `SANITIZED_EVIDENCE.md` - human-readable staging evidence summary.
- `evidence/de-staging-evidence.sanitized.json` - machine-readable sanitized
  evidence snapshot.
- `assets/drivedesk-core-demo-overview.png` - public demo screenshot.

The public repository export also generates:

- `docs/openapi.json` - FastAPI OpenAPI schema from the exported API.
- `apps/admin/public-demo/index.html` - static fake-data product demo shell.
- `GET /demo/public` - read-only synthetic demo payload in the exported API.
- `workflow`, `timeline`, and `domainEvents` - synthetic workflow contract in
  the public demo payload.
- `scripts/run_public_demo_local.sh` - one-command local API run.
- `scripts/check_public_demo_api.sh` - local API contract and client-example smoke.
- `scripts/generate_public_demo_sdk.py` - generated SDK builder from OpenAPI.
- `scripts/check_public_demo_sdk.sh` - generated SDK drift and runtime smoke.
- `sdk/generated/public-demo/` - generated Python, JavaScript, and TypeScript
  client artifacts.
- `examples/curl/demo-public.sh` - curl client example.
- `examples/python/demo_public_client.py` - Python client example.
- `examples/js/demo-public-fetch.js` - JavaScript fetch client example.
- `PUBLIC_EXPORT_MANIFEST.md` - file list and export boundary summary.

Hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

## Reviewer Path

1. Open the hosted demo.
2. Review the generated OpenAPI schema.
3. Run `bash scripts/check_public_demo_api.sh`.
4. Run one client example from `examples/`.
5. Read the API-backed demo overview.
6. Read the workflow demo overview.
7. Read the auth foundation overview.
8. Read the generated client SDK overview.
9. Read the system design overview.
10. Read the integration adapters overview.
11. Read the integration observability overview.
12. Read the case study.
13. Check CI and public demo health workflow results.
14. Run the public smoke checks locally.

## Human Explanation

The private repository keeps building the real product. This folder is the
clean explanation layer for hiring and public review: what was built, why it was
built that way, what checks exist, and how the architecture can evolve.

The export release gate makes this repeatable. Instead of manually copying
files, the private source builds a fresh public package, validates the schema,
runs public smoke checks, validates the demo shell, and leaves the result ready
for a separate public repository.
