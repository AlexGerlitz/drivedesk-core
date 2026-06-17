# DriveDesk Public Demo Plan

The public demo should let an external reviewer understand DriveDesk without
using the private staging runtime.

## Demo Goals

- show the product direction;
- show API and workflow behavior with fake data;
- show engineering quality through CI, docs, tests, and architecture;
- keep a public demo health workflow for the hosted surface;
- keep operational tooling separate from the reviewer-facing demo.

## Demo Surface

Recommended first public demo:

- a small hosted web shell or static frontend;
- fake tenant and fake users;
- read-only or resettable workflows;
- public OpenAPI docs generated from the demo API;
- public demo screenshot in the repository README;
- link to the public repository and case study.

## Demo Data

Use synthetic data only:

- sample tenants;
- sample users;
- sample memberships;
- sample audit events;
- sample outbox events;
- sample driving-school domain objects later.

## Review Flow

An external reviewer should be able to:

1. Read the public case study.
2. Inspect architecture diagrams.
3. Inspect `docs/openapi.json` for the API contract.
4. Run the public repo locally.
5. Open `https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/`.
6. See fake operational workflows.
7. Read sanitized evidence that staging checks, metrics, logs, and alerts exist.

## Runtime Boundary

The public demo is a product-review surface. The private staging runtime remains
the engineering surface for deploy, observability, and alerting practice.

The public demo does not need direct access to Prometheus, Grafana, Loki,
Alertmanager, SSH, production backups, or private GitHub Actions secrets.

## First Implementation Slice

1. Generate OpenAPI schema from the FastAPI app during public export.
2. Add public demo seed data.
3. Build a read-only admin shell.
4. Add tests and public export checks for the shell.
5. Publish the static shell through GitHub Pages.
6. Add a public health endpoint and public CI badge.
7. Link the hosted demo from the public README.
