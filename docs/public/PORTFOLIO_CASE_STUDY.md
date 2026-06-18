# DriveDesk Engineering Case Study

DriveDesk is a backend and DevOps foundation for a business operations platform.
The first domain is driving-school operations, but the Core is shaped around
generic platform capabilities: tenants, users, roles, audit events, outbox
events, workers, integrations, observability, release checks, and runbooks.

## Problem

Small operational businesses often grow through disconnected tools: chat,
spreadsheets, manual payments, ad-hoc notifications, and separate accounting or
legal systems. That creates repeated work and weak operational visibility.

DriveDesk approaches the problem as a system of action:

- staff work in one operational workspace;
- external systems connect through adapters;
- important actions are auditable;
- background work flows through an outbox;
- infrastructure has health, metrics, logs, alerts, and evidence from the
  beginning.

## Current Engineering Scope

Implemented foundation:

- FastAPI backend;
- PostgreSQL data model and Alembic migrations;
- Redis wiring;
- background worker;
- tenant, user, membership, RBAC, audit, and outbox primitives;
- credential auth foundation with bearer access tokens and `/auth/me`;
- token revocation, auth attempt recording, and auth audit events;
- redacted tenant-scoped auth session listing for admins;
- admin-triggered auth session revocation for tenant and platform operators;
- dedicated platform-admin grant model and API endpoints;
- aggregate auth metrics for sessions and login-attempt outcomes;
- auth security alert rules and runbook mapping for aggregate auth signals;
- token-backed tenant-aware RBAC checks for Core tenant endpoints;
- tenant isolation for bearer-token list/read access and global bootstrap endpoints;
- reusable tenant-scope helper module for Core list queries;
- tenant-owned business record foundation for contracts, payments, lessons, tasks, and documents;
- business record lifecycle transition endpoint with audit, outbox, and aggregate metrics;
- business record lifecycle policy catalog with tenant-scoped transition preview;
- tenant-owned workflow rules for business record status automation;
- workflow rule audit, configured outbox handoff, and aggregate workflow metrics;
- workflow actions for task record creation and adapter sync requests;
- fake file import adapter with retry and dead-letter states;
- runtime adapter catalog for executable adapter metadata;
- tenant-owned integration connection profiles with safe config and mapping;
- mapping validation against runtime adapter requirements;
- tenant-scoped operator review queue for retry and dead-letter integration jobs;
- integration adapter metrics grouped by adapter and status;
- structured adapter worker logs for started, completed, failed, and
  dead-lettered jobs;
- structured JSON API and worker logs;
- Prometheus metrics;
- Grafana dashboard;
- Loki log collection through Grafana Alloy;
- Alertmanager with Prometheus alert rules;
- SLO and runbook documentation;
- GitHub Actions CI, deploy, health, and evidence workflows;
- Docker Compose local and staging runtime.
- public demo Integration Health panel with synthetic adapter health data.
- read-only `GET /demo/public` endpoint for API-backed public demo mode.
- one-command local API demo run.
- public demo API smoke that validates health, readiness, OpenAPI, and example clients.
- curl, Python, and JavaScript public demo clients for `GET /demo/public`.
- generated OpenAPI client SDK artifacts for Python, JavaScript, and TypeScript.
- public-safe synthetic backup/restore drill with machine-readable evidence.
- public-safe synthetic release rollback drill with machine-readable evidence.
- public-safe OpenTofu plan evidence with environment model, component model,
  state boundary, secret boundary, and zero-destroy plan-only summary.
- public-safe GitOps image promotion/drift evidence with candidate tag,
  rollback tag, desired state, observed state, and synthetic `OutOfSync`.
- public-safe GitOps drift remediation evidence with plan-only reconcile,
  rollback, block, approval, and audit-event context.
- public-safe GitOps image automation evidence with candidate digest, SBOM,
  scanner result, provenance, and pull-request-only update proposal.
- synthetic business workflow in the public demo payload:
  lead -> student -> contract -> audit -> outbox -> integration sync.

## Architecture Choice

DriveDesk starts as a modular monolith.

That choice keeps local development and deployment simple while the domain is
still changing. Boundaries are still explicit:

- `apps/api` owns HTTP/API behavior;
- `apps/worker` owns background processing;
- `packages/core` owns domain primitives;
- database migrations live with the API;
- outbox events create a future path for integrations and async delivery.

Services can be extracted later if there is a real operational reason.

The public system design overview in `docs/public/SYSTEM_DESIGN.md` explains
the runtime layers, request flow, adapter boundary, and public/private export
boundary.

## DevOps Story

The staging runtime is private and fake-data only. It is treated like a real
service:

- deployed by GitHub Actions;
- checked by health and readiness probes;
- monitored by Prometheus;
- observed through Grafana;
- logs collected by Loki and Alloy;
- alerts evaluated by Prometheus and routed through Alertmanager;
- evidence artifacts collected by GitHub Actions.

This creates a practical DevOps loop:

```text
code change -> CI -> deploy -> health check -> evidence -> runbook-backed operations
```

## Current Tradeoffs

- Authentication now has a token-backed foundation with logout, failed-attempt
  tracking, redacted session listing, admin-triggered session revocation,
  aggregate metrics, auth alert rules, and platform audit events. Development
  actor headers still exist as a bootstrap path for local setup and early data
  creation.
- Platform-level tenant and user creation now has a dedicated platform-admin
  bearer-token path. A tenant owner can operate inside their tenant, but not
  create global platform records through a bearer token.
- Tenant filtering is centralized for current tenant/user list queries so
  future tenant-owned models can reuse the same pattern.
- Tenant-owned repository helpers now wrap current membership, audit, and outbox
  list queries plus the first product-shaped business records, so future
  business entities do not copy raw `tenant_id` filters.
- Business record status changes now produce `business_record.status_changed`
  audit/outbox events and aggregate `drivedesk_business_records` metrics, while
  keeping titles, external refs, payloads, tenant ids, and user ids out of
  metrics.
- Business record lifecycle policies now expose expected status paths for
  contracts, payments, lessons, tasks, and documents, plus a tenant-scoped
  preview endpoint for proposed transitions.
- Workflow rules can now react to `business_record.status_changed`, write
  `workflow.rule.triggered` audit events, enqueue configured workflow outbox
  events such as `workflow.contract_approved`, and expose only aggregate
  `drivedesk_workflow_rules` metrics.
- Workflow actions can now create tenant-owned task records and request adapter
  sync work such as `workflow.contract_sync.requested`, while keeping execution
  behind audit and outbox boundaries.
- Workflow action runs now record which automation action was created and which
  task/outbox result it produced, exposing only aggregate
  `drivedesk_workflow_action_runs` metrics.
- Outbox recovery now lets reviewed `retry` and `dead_letter` jobs move back to
  `pending` through an audited `outbox_event.retry_requested` operator action.
- Integration connections now let tenant-owned adapter profiles drive file import
  jobs through `integration_connection_id`, with aggregate
  `drivedesk_integration_connections` metrics.
- The runtime adapter catalog now exposes `GET /integration-adapters`, allowing
  UI, generated clients, and smoke tests to discover executable adapter metadata
  instead of hardcoding adapter assumptions.
- Integration connection creation now validates required mapping keys and
  rejects unsupported connection-profile adapters before outbox work is created.
- Integration mapping transform now normalizes provider-shaped fields such as
  `lead_id` and `full_name` before worker execution, with a read-only preview
  endpoint for operator review.
- Integration connection scopes now separate preview and execution permissions,
  so stored profiles can be limited to `file_import:preview` or
  `file_import:execute`.
- Runtime adapter operation contracts now describe operation keys, endpoints,
  events, required scopes, idempotency keys, and retry/dead-letter behavior.
- Integration operator review now turns failed `retry` and `dead_letter` jobs
  into safe review cards with operation keys, required scopes, redacted payload
  summaries, recommended actions, and audited retry endpoints.
- The hosted public demo uses static fallback on GitHub Pages and can be pointed
  at `GET /demo/public` for API-backed fake data, including workflow stages,
  timeline, domain events, audit, and outbox state.
- Backup/restore evidence now has a public-safe drill that creates a synthetic
  temporary database, writes a backup, restores it into a separate temporary
  database, and checks counts, schema, integrity, and redaction boundaries.
- Release rollback evidence now has a public-safe drill that promotes a bad
  candidate release, detects the readiness failure, rolls back to the stable
  release, and records `release.rollback.executed` evidence.
- SLO canary gate evidence now has a public-safe drill that evaluates a
  synthetic candidate against availability, p95 latency, and burn-rate
  thresholds, blocks promotion, and records `release.canary_gate.blocked`
  evidence.
- Staged promotion evidence now has a public-safe drill that moves a safe
  synthetic release through build, staging, canary, and production gates,
  records production approval, and emits `release.staged_promotion.completed`
  evidence.
- Helm chart foundation now packages the modular monolith into Kubernetes-style
  API, worker, migration, service, config, runtime Secret reference, and probe
  contracts without changing the app into microservices.
- OpenTofu plan evidence now describes the target infrastructure contract,
  environments, components, encrypted-state expectation, secret boundary, and
  plan-only zero-destroy summary without provisioning cloud resources.
- GitOps delivery foundation now connects the Helm chart to Argo CD-style
  build, staging, canary, and production desired state.
- GitOps image automation now records the image digest, SBOM, Trivy scan
  result, provenance, target GitOps files, and `gitops.image_update.proposed`
  audit context without mutating a registry or cluster directly.
- Alertmanager currently uses an internal receiver; external notification
  routing is a later step.
- The frontend is intentionally not the center of the current work; the backend
  and operations foundation come first.

## Next Engineering Steps

Recommended next slices:

1. Broader generated API clients from OpenAPI for more endpoints.
2. Additional mock adapters for webhook and accounting export flows.
3. More workflow rule actions for notifications, approvals, and mapping-specific adapter jobs.
4. More deployment evidence around private runtime rollout checks.
5. Public-safe infrastructure state drift evidence.

## Interview Summary

DriveDesk is not a toy CRUD app. It is a practical modular-monolith platform
with CI/CD, metrics, logs, alerts, SLOs, runbooks, and evidence workflows. The
project is intentionally built in layers so each DevOps component answers a real
operational question. The public workflow demo also shows how business actions
become timeline entries, domain events, audit records, and retryable integration
handoff.
