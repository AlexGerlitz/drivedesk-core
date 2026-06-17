# Project Direction

DriveDesk Core is a modular monolith backend foundation for a business
operations platform.

The project starts with generic platform capabilities:

- tenants;
- users;
- memberships;
- RBAC;
- audit;
- outbox events;
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
docs           architecture notes and ADRs
tests          API and foundation tests
```

## Next Work

Recommended next slices:

- real authentication;
- tenant-scoped authorization checks backed by memberships;
- structured logging;
- OpenTelemetry tracing;
- metrics endpoint;
- integration adapter examples with mock providers.
