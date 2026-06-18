# ADR-0049: Public-Safe GitOps Promotion And Drift Evidence

Status: accepted

## Context

DriveDesk has a public-safe GitOps layout with Argo CD project and application
manifests. The next delivery question is:

```text
Can image promotion and drift detection be demonstrated without exposing a live
cluster or runtime data?
```

The public repository must not contain live cluster endpoints, runtime
connection values, raw logs, or production data.

## Decision

Add public-safe GitOps promotion and drift evidence:

```text
infra/gitops/promotion/image-promotion.yaml
infra/gitops/drift/desired-state.yaml
infra/gitops/drift/observed-state.yaml
```

Add an executable check:

```text
scripts/check_public_gitops_promotion_drift.sh
```

The check validates candidate image metadata, previous image rollback context,
promotion gates, desired state, observed state, drift detection, and the
redaction boundary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/gitops-promotion-drift.sanitized.json
```

It records the image promotion and drift-detection shape without live cluster
endpoints, addresses, credentials, raw logs, runtime connection values, or
production data.

## Consequences

- The public project now demonstrates the control loop after GitOps manifests:
  promote, compare, detect drift, and keep rollback context.
- The evidence remains synthetic and reviewer-readable.
- This is not a claim that a public cluster exists.
