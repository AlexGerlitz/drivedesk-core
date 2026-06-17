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
- structured JSON API and worker logs;
- Prometheus metrics;
- Grafana dashboard;
- Loki log collection through Grafana Alloy;
- Alertmanager with Prometheus alert rules;
- SLO and runbook documentation;
- GitHub Actions CI, deploy, health, and evidence workflows;
- Docker Compose local and staging runtime.

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
- The public demo is planned but not exposed yet.
- Alertmanager currently uses an internal receiver; external notification
  routing is a later step.
- The frontend is intentionally not the center of the current work; the backend
  and operations foundation come first.

## Next Engineering Steps

Recommended next slices:

1. Public demo with fake data and a read-only workflow.
2. Backup and restore evidence for the staging runtime.
3. Real authentication and tenant-scoped memberships.
4. OpenAPI publishing and generated API client examples.
5. First mock integration adapter with retries and dead-letter handling.

## Interview Summary

DriveDesk is not a toy CRUD app. It is a practical modular-monolith platform
with CI/CD, metrics, logs, alerts, SLOs, runbooks, and evidence workflows. The
project is intentionally built in layers so each DevOps component answers a real
operational question.
