# Project Direction

DriveDesk Core is a modular monolith backend foundation for a business
operations platform.

The project starts with generic platform capabilities:

- tenants;
- users;
- memberships;
- RBAC;
- tenant isolation;
- tenant-scope query helpers;
- tenant-owned repository helpers;
- audit;
- outbox events;
- workflow rules;
- worker processing;
- Docker Compose local runtime;
- CI checks.

## Engineering Goal

The goal is to build a backend that can grow from a simple local runtime into a
production-grade platform without jumping into premature microservices.

## Repository Shape

```text
apps/api       FastAPI application
apps/worker    background worker
apps/admin     future frontend workspace
packages/core  domain primitives
infra/docker   local Docker runtime
infra/helm     Kubernetes packaging foundation
infra/gitops   Argo CD GitOps delivery foundation
infra/opentofu public-safe IaC plan and state drift evidence
infra/runtime-rollout public-safe private staging rollout evidence
infra/state-validation public-safe private infrastructure validation evidence
infra/state-remediation public-safe private infrastructure remediation plan and execution evidence
docs           architecture notes and ADRs
tests          API and foundation tests
```

## Next Work

Recommended next slices:

- richer workflow rule actions;
- structured logging;
- OpenTelemetry tracing;
- metrics endpoint;
- integration adapter examples with mock providers.
- runtime adapter catalog metadata.
