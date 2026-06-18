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
