# DriveDesk Public Roadmap

This roadmap is the public-safe engineering direction for DriveDesk Core. It
describes the platform work without exposing private infrastructure, customer
operations, or commercial details.

## Now

- Core modular monolith foundation.
- FastAPI health, readiness, and metrics endpoints.
- Tenant, user, membership, RBAC, audit, and outbox primitives.
- Fake file import adapter with retry and dead-letter state.
- Integration observability for adapter metrics, structured logs, and failed-job runbooks.
- Public demo shell with synthetic data and an API-backed synthetic contract.
- Synthetic workflow payload with stages, timeline, domain events, audit, and outbox.
- One-command local demo API run.
- API contract smoke for `/demo/public`, OpenAPI, and public client examples.
- Curl, Python, and JavaScript public demo client examples.
- Generated OpenAPI client SDK example and SDK smoke.
- Public export gate, public CI, and GitHub Pages demo.
- Public system design overview for reviewers.

## Next

- More structured adapter contracts and mapping examples.
- More public-safe workflow examples that reuse the same event and outbox shape.
- More public-safe evidence around local run, CI, OpenAPI, and demo health.
- Broader generated client SDK examples from the OpenAPI schema.

## Later

- Authentication foundation.
- Workflow automation examples.
- Integration adapter SDK examples.
- Public observability examples with fake metrics.
- Deeper admin frontend shell.

## Human Explanation

The private repository remains the real product source. The public repository is
the clean engineering surface: enough code, docs, demo, and CI to review the
architecture and execution quality without exposing private operations.
