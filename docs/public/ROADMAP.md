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
- Credential auth foundation with bearer access tokens and `/auth/me`.
- Token revocation with `POST /auth/logout`.
- Auth attempt recording, login guard, and auth audit events.
- Token-backed RBAC context for existing Core endpoints.
- Tenant-aware permission checks for tenant endpoint reads and writes.
- Bearer-token tenant isolation for tenant/user listing and global bootstrap endpoints.
- Reusable tenant-scope helper module for Core list queries.
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
- Admin-visible auth session listing.
- Dedicated platform-admin model.
- Tenant-scoped repository helpers for future tenant-owned entities.
- More public-safe workflow examples that reuse the same event and outbox shape.
- More public-safe evidence around local run, CI, OpenAPI, and demo health.
- Broader generated client SDK examples from the OpenAPI schema.

## Later

- Workflow automation examples.
- Integration adapter SDK examples.
- Public observability examples with fake metrics.
- Deeper admin frontend shell.

## Human Explanation

The private repository remains the real product source. The public repository is
the clean engineering surface: enough code, docs, demo, and CI to review the
architecture and execution quality without exposing private operations.
