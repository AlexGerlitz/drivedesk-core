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
- Public demo shell with synthetic data.
- Public export gate, public CI, and GitHub Pages demo.
- Public system design overview for reviewers.

## Next

- Public demo health workflow.
- Read-only API-backed demo mode.
- More structured adapter contracts and mapping examples.
- More public-safe evidence around CI, OpenAPI, and demo health.

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
