# Sanitized Engineering Evidence

This document summarizes a private staging evidence run in a public-safe form.
It keeps the engineering facts while omitting private hostnames, addresses,
internal paths, credentials, and raw logs.

## Evidence Snapshot

Source file:

```text
docs/public/evidence/de-staging-evidence.sanitized.json
```

Recovery drill source file:

```text
docs/public/evidence/backup-restore-drill.sanitized.json
```

Release rollback drill source file:

```text
docs/public/evidence/release-rollback-drill.sanitized.json
```

SLO canary gate drill source file:

```text
docs/public/evidence/slo-canary-gate.sanitized.json
```

Staged promotion drill source file:

```text
docs/public/evidence/staged-promotion.sanitized.json
```

Helm chart validation source file:

```text
docs/public/evidence/helm-render.sanitized.json
```

OpenTofu plan validation source file:

```text
docs/public/evidence/opentofu-plan.sanitized.json
```

GitOps layout validation source file:

```text
docs/public/evidence/gitops-layout.sanitized.json
```

GitOps promotion and drift validation source file:

```text
docs/public/evidence/gitops-promotion-drift.sanitized.json
```

GitOps drift remediation validation source file:

```text
docs/public/evidence/gitops-drift-remediation.sanitized.json
```

GitOps image automation validation source file:

```text
docs/public/evidence/gitops-image-automation.sanitized.json
```

Verified signals:

- CI completed successfully;
- staging deploy completed successfully;
- staging health workflow completed successfully;
- staging evidence workflow completed successfully;
- API listener was private;
- Prometheus listener was private;
- Grafana listener was private;
- Loki listener was private;
- Grafana Alloy listener was private;
- Alertmanager listener was private;
- Prometheus scraped required targets;
- Loki returned recent API logs;
- Alertmanager was ready;
- Prometheus loaded alert rules;
- active alerts count was zero at collection time.
- the public synthetic backup/restore drill created a temporary backup artifact;
- the restore target passed integrity checks;
- restored row counts matched the source counts;
- production data was not touched.
- the public synthetic release rollback drill promoted a candidate release;
- the candidate readiness failure was detected;
- rollback returned `current` to the stable release;
- `release.rollback.executed` evidence was recorded.
- the public synthetic SLO canary gate drill evaluated stable and candidate
  release metrics;
- availability, p95 latency, and error budget burn violations were detected;
- candidate promotion was blocked;
- `release.canary_gate.blocked` evidence was recorded.
- the public synthetic staged promotion drill moved a safe release through
  build, staging, canary, and production gates;
- synthetic production approval was recorded;
- promotion history was hashed;
- `release.staged_promotion.completed` evidence was recorded.
- the public Helm chart foundation contains API, worker, migration, service,
  config, runtime Secret reference, and probe templates;
- chart values schema was validated;
- private infrastructure markers were absent from the chart.
- the public OpenTofu plan evidence records build, staging, canary, and
  production environment names;
- infrastructure components are described as a public-safe contract;
- encrypted state, state locking, and secret exclusion boundaries are recorded;
- the public OpenTofu evidence is plan-only and has zero destroy operations.
- the public GitOps delivery foundation contains Argo CD project, application,
  environment, and promotion metadata;
- Argo CD applications reference the Helm chart path;
- build, staging, canary, and production overlays were validated;
- public-safe evidence gates are referenced by the promotion order.
- the public GitOps promotion manifest records the candidate image tag;
- the previous release tag is preserved as rollback context;
- desired state is compared with observed state;
- synthetic production drift is detected and marked `OutOfSync`.
- the public GitOps remediation policy defines reconcile, rollback, and block
  actions;
- production remediation requires approval;
- remediation is recorded as plan-only and does not mutate a cluster;
- rollback context is attached to the drift remediation decision;
- `gitops.drift_remediation.planned` evidence is recorded.
- the public GitOps image automation manifest records candidate image tag and
  digest;
- SBOM, vulnerability scanner, zero critical/high finding, and provenance
  metadata are attached to the synthetic build artifact;
- the image update proposal targets GitOps manifests instead of mutating a
  registry or cluster directly;
- the proposal is pull-request-only and records
  `gitops.image_update.proposed` evidence.

## Human Explanation

The evidence proves that the project is not just code in a repository. A real
staging runtime was deployed, checked, observed, and summarized by automation.
The public version keeps only the operational shape and health results.

## What This Shows

- CI/CD is wired end to end.
- Health and readiness checks exist.
- Metrics are collected.
- Logs are collected.
- Alert rules are loaded.
- Alertmanager is reachable.
- Evidence is machine-readable.
- Backup/restore is checked through an executable public drill.
- Bad-release rollback is checked through an executable public drill.
- SLO canary promotion is checked through an executable public drill.
- Staged release promotion is checked through an executable public drill.
- Helm chart packaging is checked through an executable public validation.
- OpenTofu infrastructure shape is checked through an executable public
  validation.
- GitOps desired-state delivery is checked through an executable public
  validation.
- GitOps image promotion and drift detection are checked through an executable
  public validation.
- GitOps drift remediation is checked through an executable public validation.
- GitOps image automation is checked through an executable public validation.

## What This Leaves Out

The public evidence omits raw logs, request bodies, private infrastructure
labels, credentials, internal hostnames, and server-specific addresses.
