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
- fake file import adapter with retry and dead-letter states;
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

- Authentication is still a development foundation based on actor headers.
- The hosted public demo uses static fallback on GitHub Pages and can be pointed
  at `GET /demo/public` for API-backed fake data.
- Alertmanager currently uses an internal receiver; external notification
  routing is a later step.
- The frontend is intentionally not the center of the current work; the backend
  and operations foundation come first.

## Next Engineering Steps

Recommended next slices:

1. Backup and restore evidence for the staging runtime.
2. Real authentication and tenant-scoped memberships.
3. Generated API client examples from OpenAPI.
4. Additional mock adapters for webhook and accounting export flows.
5. Read-only demo API client examples.

## Interview Summary

DriveDesk is not a toy CRUD app. It is a practical modular-monolith platform
with CI/CD, metrics, logs, alerts, SLOs, runbooks, and evidence workflows. The
project is intentionally built in layers so each DevOps component answers a real
operational question.
