# GitOps Delivery Foundation

DriveDesk includes a public-safe GitOps delivery foundation for Argo CD-style
cluster delivery.

## Command

```bash
bash scripts/check_public_gitops_layout.sh
```

## What The Check Does

The check validates the GitOps layout:

```text
public repository
    |
    v
Argo CD AppProject
    |
    v
Applications for build, staging, canary, and production
    |
    v
Helm chart path plus environment values
```

The check verifies:

- GitOps files are present;
- Argo CD project manifest exists;
- Argo CD application manifests exist;
- public repository source is used;
- the Helm chart path is referenced;
- environment value files are referenced;
- build, staging, canary, and production overlays exist;
- runtime connection values stay behind Kubernetes Secret references;
- staged promotion order is recorded;
- release evidence gates are referenced;
- private infrastructure markers are absent;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_gitops_layout",
  "data_profile": "synthetic_demo_data",
  "delivery_model": "argocd_gitops",
  "checks": {
    "argocd_project_present": true,
    "argocd_applications_present": true,
    "helm_chart_path_referenced": true,
    "environment_overlays_present": true,
    "staged_promotion_order_present": true,
    "evidence_gates_referenced": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public GitOps layer uses public repository references, synthetic image tags,
cluster-internal destination names, and external runtime Secret references. It
does not include live cluster endpoints, server-specific addresses, raw logs,
runtime connection values, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/gitops-layout.sanitized.json
```

## Why This Matters

Docker Compose proves local runtime shape. Helm proves Kubernetes packaging.
GitOps proves how the desired state can move through build, staging, canary, and
production in a repeatable, reviewable way.
