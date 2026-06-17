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
shell: tenant, health, metrics, work queue, members, audit events, outbox
events, adapter contracts, sync jobs, and Integration Health.

## Runtime Modes

| Mode | Behavior |
| --- | --- |
| Static fallback | GitHub Pages loads `demo-data.js` and works without a backend. |
| API-backed | The demo shell loads JSON from `GET /demo/public` when `?demoApi=...` is provided. |

Example local API-backed run:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core uvicorn drivedesk_api.main:app --reload --port 8080
```

Then open the static demo with:

```text
apps/admin/public-demo/index.html?demoApi=http://localhost:8080/demo/public
```

## Safety Boundary

The endpoint is read-only and fake-data only:

- no production database access is required;
- no private infrastructure details are returned;
- no personal data is returned;
- no credentials or server paths are returned;
- GitHub Pages can still run without an API.

## Human Explanation

This is the first public frontend/backend contract. The static demo remains
stable for reviewers, while the same UI can be pointed at the FastAPI endpoint
to prove that the backend owns the demo payload shape.
