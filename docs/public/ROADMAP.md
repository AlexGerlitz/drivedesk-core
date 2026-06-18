# DriveDesk Public Roadmap

This roadmap is the public-safe engineering direction for DriveDesk Core. It
describes the platform work without exposing private infrastructure, customer
operations, or commercial details.

## Now

- Core modular monolith foundation.
- FastAPI health, readiness, and metrics endpoints.
- Tenant, user, membership, RBAC, audit, and outbox primitives.
- Fake file import adapter with retry and dead-letter state.
- Runtime adapter catalog with `GET /integration-adapters`.
- Tenant-owned integration connection profiles with safe config and mapping.
- Integration connection scopes for preview and execution boundaries.
- Structured adapter operation contracts in the runtime catalog.
- Tenant-scoped operator review queue for retry and dead-letter integration jobs.
- Mapping validation against runtime adapter requirements.
- Runtime mapping transform and read-only mapping preview.
- Integration observability for adapter metrics, structured logs, and failed-job runbooks.
- Outbox recovery endpoint for audited operator retry of failed integration jobs.
- Credential auth foundation with bearer access tokens and `/auth/me`.
- Token revocation with `POST /auth/logout`.
- Admin-visible redacted auth session listing with `GET /auth/sessions`.
- Admin-triggered visible session revocation with `POST /auth/sessions/{session_id}/revoke`.
- Dedicated platform-admin grants with `POST /platform/admins` and `GET /platform/admins`.
- Auth attempt recording, login guard, and auth audit events.
- Aggregate auth metrics for session lifecycle and login-attempt outcomes.
- Auth security alert names and public-safe runbook shape.
- Token-backed RBAC context for existing Core endpoints.
- Tenant-aware permission checks for tenant endpoint reads and writes.
- Bearer-token tenant isolation for tenant/user listing and global bootstrap endpoints.
- Reusable tenant-scope helper module for Core list queries.
- Reusable tenant-owned repository helper module for models with `tenant_id`.
- Tenant-owned business record foundation for contracts, payments, lessons, tasks, and documents.
- Business record lifecycle transition endpoint with audit, outbox, and aggregate metrics.
- Business record lifecycle policy catalog and tenant-scoped transition preview.
- Tenant-owned workflow rule foundation for `business_record.status_changed` automation.
- Workflow rule audit, configured outbox handoff, and aggregate workflow metrics.
- Workflow actions for task-record creation and adapter-sync requests.
- Workflow action run history with task/outbox links and aggregate action-run metrics.
- Public demo shell with synthetic data and an API-backed synthetic contract.
- Synthetic workflow payload with stages, timeline, domain events, audit, and outbox.
- One-command local demo API run.
- API contract smoke for `/demo/public`, OpenAPI, and public client examples.
- Curl, Python, and JavaScript public demo client examples.
- Generated OpenAPI client SDK example and SDK smoke.
- Public export gate, public CI, and GitHub Pages demo.
- Public system design overview for reviewers.
- Public-safe synthetic backup/restore drill and sanitized evidence snapshot.
- Public-safe synthetic release rollback drill and sanitized evidence snapshot.

## Next

- More public-safe workflow examples that reuse the same rule, action-run, task,
  event, and outbox shape.
- More public-safe evidence around local run, CI, OpenAPI, and demo health.
- Broader generated client SDK examples from the OpenAPI schema.
- More adapter recovery examples with payload mapping and follow-up actions.
- More deployment evidence around canary gates, staged promotion, and SLO burn.

## Later

- Richer workflow automation examples with notification, approval, and mapping actions.
- Integration adapter SDK examples.
- Broader public observability examples with fake metrics.
- Deeper admin frontend shell.

## Human Explanation

The private repository remains the real product source. The public repository is
the clean engineering surface: enough code, docs, demo, and CI to review the
architecture and execution quality without exposing private operations.
