# Helm Chart Foundation

DriveDesk includes a public-safe Helm chart foundation for Kubernetes-style
deployment packaging.

## Command

```bash
bash scripts/check_public_helm_render.sh
```

## What The Check Does

The check validates the chart structure and, when the Helm binary is available,
renders the chart with public-safe values:

```text
Chart metadata
    |
    v
values and schema
    |
    v
API Deployment, worker Deployment, migration Job, Service, ConfigMap
    |
    v
external runtime Secret references and HTTP probes
```

The check verifies:

- chart files are present;
- chart metadata is valid;
- values schema is valid JSON;
- public values are present;
- API Deployment template exists;
- worker Deployment template exists;
- migration Job template exists;
- Service template exists;
- runtime connection strings are referenced through Kubernetes Secret keys;
- liveness and readiness probes are present;
- private infrastructure markers are absent;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_helm_chart_render",
  "data_profile": "synthetic_demo_data",
  "deployment_model": "kubernetes_helm_chart",
  "checks": {
    "chart_files_present": true,
    "values_schema_valid": true,
    "api_deployment_template_present": true,
    "worker_deployment_template_present": true,
    "migration_job_template_present": true,
    "runtime_secret_refs_present": true,
    "health_probes_present": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public chart uses synthetic image values and external runtime Secret
references. It does not include private deployment paths, hostnames, addresses,
credentials, raw logs, production data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/helm-render.sanitized.json
```

## Why This Matters

Docker Compose proves local runtime shape. Helm proves the next packaging step:
the same modular monolith can be deployed through Kubernetes-style primitives
without changing the application into premature microservices.
