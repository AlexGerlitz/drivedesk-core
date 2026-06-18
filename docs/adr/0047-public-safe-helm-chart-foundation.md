# ADR-0047: Public-Safe Helm Chart Foundation

Status: accepted

## Context

DriveDesk has a stable Docker Compose foundation, public CI, release safety
drills, and public-safe evidence for backup, rollback, canary gates, and staged
promotion. The next DevOps question is:

```text
Can the modular monolith be packaged for Kubernetes-style deployment without
changing the architecture into premature microservices?
```

The public repository must not contain private deployment targets, hostnames,
runtime connection values, raw logs, or production data.

## Decision

Add a public-safe Helm chart foundation:

```text
infra/helm/drivedesk-core
```

The chart includes:

- API Deployment;
- worker Deployment;
- migration Job;
- Service;
- ConfigMap;
- ServiceAccount;
- external runtime Secret references;
- liveness and readiness probes;
- values schema;
- public-safe values file.

Add an executable check:

```text
scripts/check_public_helm_render.sh
```

The check validates the chart structure and renders it with Helm when the Helm
binary is available. If Helm is not available, the static chart contract is
still validated through Python and CI remains useful.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/helm-render.sanitized.json
```

It records the chart shape and validation checks without private paths,
hostnames, addresses, credentials, raw logs, or production data.

## Consequences

- The public project now demonstrates a path from Docker Compose to
  Kubernetes-style packaging.
- The app remains a modular monolith; Helm packages API, worker, migrations,
  and service boundaries without forcing microservices.
- Reviewers can inspect and validate the chart without infrastructure access.
- This is not a complete production Kubernetes deployment; it is the chart
  foundation layer.
