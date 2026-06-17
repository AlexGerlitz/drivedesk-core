# ADR-0006: DriveDesk Core Foundation

Status: accepted

## Context

DriveDesk needs a clean backend foundation before adding frontend, integrations,
or infrastructure automation.

## Decision

Use this repository shape:

- `apps/api` for FastAPI;
- `apps/worker` for background jobs;
- `apps/admin` for the future frontend workspace;
- `packages/core` for domain primitives;
- `infra/docker` for local runtime.

Sprint 0 starts with health endpoints, worker heartbeat, core event primitives,
tenant/audit database tables, Docker Compose, and CI smoke checks.

## Consequences

- New product work has a clear namespace.
- API and worker can evolve separately while staying in one repository.
- Future Kubernetes and Helm work can grow from the compose contract.
