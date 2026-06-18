# DriveDesk Public Roadmap

This roadmap is the public-safe engineering direction for DriveDesk Core. It
describes the platform work without exposing private infrastructure, customer
operations, or commercial details.

Current status snapshot: `docs/public/PROJECT_STATUS.md`.
Compact system review path: `docs/public/SYSTEM_REVIEW_PATH.md`.
Fast external review path: `docs/public/REVIEWER_QUICKSTART.md`.

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
- Public system review path tying the public root, demo, API, SDK, operations
  evidence, release safety, GitOps, OpenTofu, and evidence index together.
- Public system design overview.
- Public-safe synthetic backup/restore drill and sanitized evidence snapshot.
- Public-safe synthetic release rollback drill and sanitized evidence snapshot.
- Public-safe synthetic SLO canary gate drill and sanitized evidence snapshot.
- Public-safe synthetic staged promotion drill and sanitized evidence snapshot.
- Public-safe Helm chart foundation with render validation.
- Public-safe OpenTofu plan evidence with environment, component, state, secret,
  and plan-only boundaries.
- Public-safe infrastructure state drift evidence comparing desired and
  synthetic observed infrastructure state.
- Public-safe private staging runtime rollout evidence with health,
  observability, sanitized evidence, and rollback review boundaries.
- Public-safe private infrastructure validation evidence with read-only
  staging/control-plane checks before any apply or remediation.
- Public-safe private infrastructure remediation plan evidence with operator
  review, preflight gates, rollback context, postchecks, and no public apply.
- Public-safe private infrastructure remediation execution evidence with
  reviewed execution, postchecks, rollback context, evidence refresh, and no
  production apply.
- Public-safe post-remediation drift refresh evidence with resolved drift,
  read-only recheck, and no residual or accepted drift.
- Public-safe recurring scheduled validation evidence with daily cron, manual
  dispatch fallback, missed-run guard, and clean sample runs.
- Public-safe scheduled validation alerting evidence with missed-run,
  failed-run, secret-boundary signals, runbook keys, and failure artifact route.
- Public-safe 70 percent DevOps/platform milestone evidence with seven complete
  evidence groups and an executable milestone check.
- Public-safe observability proof (`docs/public/OBSERVABILITY_PROOF.md`)
  connecting metrics, structured logs, alerts, runbooks, dashboards, and
  sanitized evidence.
- Public-safe alert routing evidence (`docs/public/ALERT_ROUTING_EVIDENCE.md`)
  connecting Alertmanager-style routes, receivers, dedupe keys, escalation,
  silences, runbooks, and sanitized evidence.
- Public-safe GitOps delivery foundation with Argo CD layout validation.
- Public-safe GitOps image promotion and drift detection evidence.
- Public-safe GitOps drift remediation evidence with approval and rollback context.
- Public-safe GitOps image automation evidence with digest, SBOM, scan,
  provenance, and pull-request-only proposal metadata.

## Next

- More public-safe workflow examples that reuse the same rule, action-run, task,
  event, and outbox shape.
- More public-safe evidence around local run, CI, OpenAPI, and demo health.
- More adapter recovery examples with payload mapping and follow-up actions.
- More evidence around external notification adapters once destinations and
  secrets are intentionally configured outside the public surface.
- Broader generated client SDK examples from the OpenAPI schema.

## Later

- Richer workflow automation examples with notification, approval, and mapping actions.
- Integration adapter SDK examples.
- Richer public observability examples with synthetic dashboard evidence.
- Deeper admin frontend shell.

## Engineering Summary

The private repository remains the real product source. The public repository is
the clean engineering surface: enough code, docs, demo, and CI to review the
architecture and execution quality without exposing private operations.
