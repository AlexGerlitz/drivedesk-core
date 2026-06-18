# ADR-0048: Public-Safe GitOps Delivery Foundation

Status: accepted

## Context

DriveDesk now has public CI, synthetic release drills, and a public-safe Helm
chart foundation. The next delivery question is:

```text
Can the Helm-packaged modular monolith be represented as GitOps desired state
without exposing live cluster details?
```

The public repository must not contain live deployment targets, runtime
connection values, raw logs, or production data.

## Decision

Add a public-safe GitOps delivery layout:

```text
infra/gitops
```

The layout includes:

- Argo CD AppProject manifest;
- Argo CD Application manifests for build, staging, canary, and production;
- environment values for each stage;
- promotion order metadata;
- references to the existing Helm chart path;
- references to public-safe release evidence gates.

Add an executable check:

```text
scripts/check_public_gitops_layout.sh
```

The check validates the GitOps files, Argo CD manifests, Helm chart references,
environment overlays, staged promotion order, evidence gates, and redaction
boundary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/gitops-layout.sanitized.json
```

It records the GitOps layout and validation checks without live cluster
endpoints, addresses, credentials, raw logs, runtime connection values, or
production data.

## Consequences

- The public project now demonstrates the path from Docker Compose to Helm to
  GitOps delivery.
- Argo CD manifests stay public-safe and reviewer-readable.
- The modular monolith remains intact; GitOps coordinates deployment state, not
  service decomposition.
- This is a desired-state foundation, not a claim that a public cluster exists.
