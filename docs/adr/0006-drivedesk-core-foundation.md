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
- `infra/helm` for Kubernetes-style packaging.
- `infra/gitops` for Argo CD desired-state delivery.

Sprint 0 starts with health endpoints, worker heartbeat, core event primitives,
tenant/audit database tables, Docker Compose, and CI smoke checks.

## Consequences

- New product work has a clear namespace.
- API and worker can evolve separately while staying in one repository.
- The Helm chart foundation packages API, worker, migrations, service, config,
  runtime Secret references, and probes without changing the modular monolith
  into premature microservices.
- The GitOps delivery foundation links the Helm chart to build, staging,
  canary, and production desired-state manifests.
- The GitOps image automation evidence layer records candidate image digest,
  SBOM, scan, provenance, and pull-request-only update proposal metadata
  without mutating a registry or cluster.
- The OpenTofu evidence layer records public-safe infrastructure shape, state
  boundary, secret boundary, and plan-only summary without provisioning cloud
  resources.
- The infrastructure state drift layer compares desired and synthetic observed
  state while preserving state, secret, and plan-only boundaries.
- The runtime rollout evidence layer connects private staging deploy, health,
  observability, and sanitized evidence gates without exposing private runtime
  details.
- The private infrastructure validation layer records a read-only validation
  boundary before any apply, deploy, restart, or remediation decision.
- The private infrastructure remediation planning layer records plan-only,
  operator-reviewed actions with preflight gates, rollback context, postchecks,
  and no public apply.
- The private infrastructure remediation execution layer records reviewed
  private staging execution, preflight gates, postchecks, rollback context,
  evidence refresh, and no production apply.
- The post-remediation drift refresh layer records a read-only recheck after
  execution, resolved drift, no residual drift, no accepted drift, and no
  runtime mutation.
