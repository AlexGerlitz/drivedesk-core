# DriveDesk GitOps Foundation

This folder contains a public-safe GitOps delivery layout for DriveDesk Core.

It connects the existing Helm chart to Argo CD-style desired state without
requiring access to a real cluster.

## Layout

```text
infra/gitops/
  argocd/
    project.yaml
    app-build.yaml
    app-staging.yaml
    app-canary.yaml
    app-production.yaml
  environments/
    build/values.yaml
    staging/values.yaml
    canary/values.yaml
    production/values.yaml
  promotion/order.yaml
  promotion/image-promotion.yaml
  drift/desired-state.yaml
  drift/observed-state.yaml
  remediation/policy.yaml
  remediation/decision.yaml
  image-automation/build-artifact.yaml
  image-automation/update-proposal.yaml
```

## Delivery Shape

```text
Git commit
  -> public CI and release gate
  -> Helm chart package
  -> Argo CD Application desired state
  -> build -> staging -> canary -> production
```

The manifests use public repository references, synthetic image tags, and
runtime Secret references only. They do not include live cluster endpoints,
server-specific addresses, raw logs, or runtime connection values.

The remediation manifests are plan-only evidence. They show how drift would be
handled through reconcile, rollback, or block decisions without applying
anything to a cluster.

The image automation manifests are proposal-only evidence. They show how a
candidate image digest, SBOM, scanner result, provenance, and target GitOps
files would be turned into a pull request instead of mutating a registry or
cluster directly.
