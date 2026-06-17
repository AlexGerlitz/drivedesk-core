# DriveDesk Public Engineering Surface

This folder contains the public-safe engineering surface for DriveDesk. It is
written so an external reviewer can understand the project without access to
private infrastructure, production history, customer data, or operational
credentials.

## Documents

- `PORTFOLIO_CASE_STUDY.md` - engineering case study and current system shape.
- `SYSTEM_DESIGN.md` - public-safe system design overview.
- `API_BACKED_DEMO.md` - read-only synthetic API contract for the public demo.
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
- `PUBLIC_EXPORT_MANIFEST.md` - file list and export boundary summary.

Hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

## Reviewer Path

1. Open the hosted demo.
2. Review the generated OpenAPI schema.
3. Read the API-backed demo overview.
4. Read the system design overview.
5. Read the integration adapters overview.
6. Read the integration observability overview.
7. Read the case study.
8. Check CI and public demo health workflow results.
9. Run the public smoke checks locally.

## Human Explanation

The private repository keeps building the real product. This folder is the
clean explanation layer for hiring and public review: what was built, why it was
built that way, what checks exist, and how the architecture can evolve.

The export release gate makes this repeatable. Instead of manually copying
files, the private source builds a fresh public package, validates the schema,
runs public smoke checks, validates the demo shell, and leaves the result ready
for a separate public repository.
