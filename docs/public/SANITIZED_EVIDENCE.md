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

Infrastructure state drift validation source file:

```text
docs/public/evidence/infra-state-drift.sanitized.json
```

Runtime rollout validation source file:

```text
docs/public/evidence/runtime-rollout.sanitized.json
```

Private infrastructure validation source file:

```text
docs/public/evidence/private-infra-validation.sanitized.json
```

Private infrastructure remediation plan source file:

```text
docs/public/evidence/private-infra-remediation-plan.sanitized.json
```

Private infrastructure remediation execution source file:

```text
docs/public/evidence/private-infra-remediation-execution.sanitized.json
```

Private infrastructure post-remediation drift refresh source file:

```text
docs/public/evidence/private-infra-post-remediation-drift-refresh.sanitized.json
```

Private infrastructure scheduled validation source file:

```text
docs/public/evidence/private-infra-scheduled-validation.sanitized.json
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
- the public infrastructure state drift evidence compares desired and observed
  synthetic state;
- observability and backup storage drift are detected;
- state backend and secret boundaries remain preserved;
- the infrastructure drift decision is plan-only and does not apply changes.
- the public runtime rollout evidence records build, deploy, runtime health,
  observability, and evidence stages;
- private staging deploy, health, and evidence results are linked through a
  sanitized summary;
- loopback-only runtime boundaries are recorded;
- rollback remains an operator-reviewed action.
- the public private infrastructure validation evidence records a read-only
  staging/control-plane validation boundary;
- runtime health, observability, OpenTofu, runtime rollout, and GitOps
  contracts are referenced by the validation evidence;
- no runtime mutation, infrastructure apply, service restart, raw logs, request
  bodies, private paths, or production data are included in public artifacts.
- the public private infrastructure remediation plan evidence carries forward
  validation and drift results into plan-only actions;
- remediation actions include operator review, preflight gates, rollback
  context, postcheck gates, and no public apply;
- `infra.remediation.plan.ready` evidence is recorded.
- the public private infrastructure remediation execution evidence records
  reviewed private staging execution after the plan;
- execution evidence includes passed preflight gates, postchecks, rollback
  context, refreshed sanitized evidence, and no production apply.
- the public private infrastructure post-remediation drift refresh evidence
  records a read-only refresh after reviewed execution;
- the previously drifted observability and backup-storage components are marked
  resolved with no residual or accepted drift in the sanitized snapshot;
- `infra.post_remediation_drift.clean` evidence is recorded.
- the public private infrastructure scheduled validation evidence records a
  recurring daily schedule, manual dispatch fallback, missed-run guard, and
  three sampled successful runs;
- the scheduled workflow rechecks post-remediation drift refresh and the public
  secret boundary;
- `infra.scheduled_validation.healthy` evidence is recorded.
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
- Infrastructure state drift is checked through an executable public
  validation.
- Runtime rollout evidence is checked through an executable public validation.
- Private infrastructure validation is checked through an executable public
  validation.
- Private infrastructure remediation planning is checked through an executable
  public validation.
- Private infrastructure remediation execution is checked through an executable
  public validation.
- Private infrastructure post-remediation drift refresh is checked through an
  executable public validation.
- Private infrastructure scheduled validation is checked through an executable
  public validation and a scheduled GitHub Actions workflow.
- GitOps desired-state delivery is checked through an executable public
  validation.
- GitOps image promotion and drift detection are checked through an executable
  public validation.
- GitOps drift remediation is checked through an executable public validation.
- GitOps image automation is checked through an executable public validation.

## What This Leaves Out

The public evidence omits raw logs, request bodies, private infrastructure
labels, credentials, internal hostnames, and server-specific addresses.
