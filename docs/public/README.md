# DriveDesk Public Engineering Surface

This folder contains the public-safe engineering surface for DriveDesk. It is
written so the project can be inspected without access to private
infrastructure, production history, customer data, or operational credentials.

## Documents

- `ENGINEERING_CASE_STUDY.md` - engineering case study and current system shape.
- `REVIEWER_QUICKSTART.md` - shortest external review path with 5-minute,
  15-minute, and 45-minute verification tracks.
- `ENGINEERING_REVIEW_GUIDE.md` - short review path for demo, CI, API, recovery, GitOps, and IaC evidence.
- `PROJECT_STATUS.md` - current public-safe engineering status, limits, and next work.
- `TECHNICAL_CAPABILITY_MAP.md` - capability-to-evidence map with verifier commands.
- `EVIDENCE_INDEX.md` - human-readable public evidence index contract.
- `ENGINEERING_PROOF.md` - proof tab payload, gates, evidence, and verifier contract.
- `OBSERVABILITY_PROOF.md` - public-safe metrics, logs, alerts, and dashboard evidence.
- `ALERT_ROUTING_EVIDENCE.md` - public-safe alert routing, dedupe, escalation, and silence evidence.
- `INCIDENT_RESPONSE_DEMO.md` - public-safe incident queue, recovery actions,
  and resolution evidence in the demo.
- `SYSTEM_DESIGN.md` - public-safe system design overview.
- `API_BACKED_DEMO.md` - read-only synthetic API contract for the public demo.
- `WORKFLOW_DEMO.md` - synthetic business workflow, timeline, events, audit,
  and outbox overview.
- `WORKFLOW_RULES.md` - tenant-owned automation rules, audit, outbox, and metrics.
- `WORKFLOW_ACTION_RUNS.md` - workflow execution history, links, and metrics.
- `AUTH_FOUNDATION.md` - credential auth, bearer token, and RBAC overview.
- `AUTH_OBSERVABILITY.md` - aggregate auth metrics, alert names, and runbook shape.
- `SESSION_REVOCATION.md` - admin-triggered tenant/platform session revocation.
- `PLATFORM_ADMIN.md` - dedicated platform-admin model and SaaS control-plane boundary.
- `TENANT_ISOLATION.md` - tenant-scoped bearer access and cross-tenant boundaries.
- `BUSINESS_RECORDS.md` - tenant-owned business record foundation.
- `BUSINESS_RECORD_LIFECYCLE.md` - lifecycle policies and transition preview.
- `CLIENT_SDK.md` - generated OpenAPI client SDK example.
- `INTEGRATION_ADAPTER_CATALOG.md` - runtime adapter metadata and discovery contract.
- `INTEGRATION_MAPPING_VALIDATION.md` - mapping validation against adapter requirements.
- `INTEGRATION_MAPPING_TRANSFORM.md` - runtime field mapping transform and preview.
- `INTEGRATION_CONNECTION_SCOPES.md` - least-privilege connection scopes.
- `INTEGRATION_OPERATION_CONTRACTS.md` - operation-level adapter contracts.
- `INTEGRATION_ACCOUNTING_EXPORT.md` - executable outbound accounting export adapter.
- `INTEGRATION_CONNECTION_DIAGNOSTICS.md` - safe connection health-checks and metrics.
- `INTEGRATION_RECONCILIATION.md` - safe provider evidence comparison and diff.
- `INTEGRATION_INCIDENT_RUNBOOKS.md` - incident cards and runbook-backed operator flow.
- `INTEGRATION_OPERATOR_REVIEW.md` - safe operator queue for failed integration jobs.
- `INTEGRATION_CONNECTIONS.md` - tenant-owned adapter profiles and mapping.
- `INTEGRATION_ADAPTERS.md` - adapter contract, outbox, retry, and dead-letter overview.
- `INTEGRATION_OBSERVABILITY.md` - adapter metrics, worker logs, and failure visibility overview.
- `OUTBOX_RECOVERY.md` - operator retry path for failed outbox events.
- `BACKUP_RESTORE_EVIDENCE.md` - public-safe synthetic backup and restore drill.
- `RELEASE_ROLLBACK_EVIDENCE.md` - public-safe bad-release rollback drill.
- `SLO_CANARY_GATE_EVIDENCE.md` - public-safe SLO canary promotion gate drill.
- `STAGED_PROMOTION_EVIDENCE.md` - public-safe staged release promotion drill.
- `HELM_CHART.md` - public-safe Helm chart foundation.
- `OPENTOFU_PLAN_EVIDENCE.md` - public-safe OpenTofu plan evidence.
- `INFRA_STATE_DRIFT_EVIDENCE.md` - public-safe infrastructure state drift evidence.
- `RUNTIME_ROLLOUT_EVIDENCE.md` - public-safe private staging runtime rollout evidence.
- `PRIVATE_INFRA_VALIDATION.md` - public-safe private infrastructure validation evidence.
- `PRIVATE_INFRA_REMEDIATION.md` - public-safe private infrastructure remediation plan evidence.
- `PRIVATE_INFRA_REMEDIATION_EXECUTION.md` - public-safe private infrastructure remediation execution evidence.
- `PRIVATE_INFRA_POST_REMEDIATION_DRIFT_REFRESH.md` - public-safe post-remediation drift refresh evidence.
- `PRIVATE_INFRA_SCHEDULED_VALIDATION.md` - public-safe recurring scheduled validation evidence.
- `PRIVATE_INFRA_SCHEDULED_ALERTING.md` - public-safe scheduled validation alerting evidence.
- `PLATFORM_MATURITY_70.md` - public-safe 70 percent DevOps/platform milestone.
- `GITOPS_DELIVERY.md` - public-safe GitOps delivery foundation.
- `GITOPS_PROMOTION_DRIFT.md` - public-safe GitOps image promotion and drift evidence.
- `GITOPS_DRIFT_REMEDIATION.md` - public-safe GitOps drift remediation evidence.
- `GITOPS_IMAGE_AUTOMATION.md` - public-safe GitOps image automation evidence.
- `ARCHITECTURE_DIAGRAMS.md` - public-safe architecture diagrams.
- `PUBLIC_DEMO_PLAN.md` - future live demo plan.
- `ROADMAP.md` - public-safe engineering roadmap.
- `SANITIZED_EVIDENCE.md` - human-readable staging evidence summary.
- `evidence/de-staging-evidence.sanitized.json` - machine-readable sanitized
  evidence snapshot.
- `evidence/backup-restore-drill.sanitized.json` - machine-readable synthetic
  backup/restore evidence snapshot.
- `evidence/release-rollback-drill.sanitized.json` - machine-readable synthetic
  release rollback evidence snapshot.
- `evidence/slo-canary-gate.sanitized.json` - machine-readable synthetic SLO
  canary gate evidence snapshot.
- `evidence/staged-promotion.sanitized.json` - machine-readable synthetic staged
  promotion evidence snapshot.
- `evidence/helm-render.sanitized.json` - machine-readable Helm chart validation
  evidence snapshot.
- `evidence/opentofu-plan.sanitized.json` - machine-readable OpenTofu plan
  evidence snapshot.
- `evidence/infra-state-drift.sanitized.json` - machine-readable infrastructure
  state drift evidence snapshot.
- `evidence/runtime-rollout.sanitized.json` - machine-readable private staging
  runtime rollout evidence snapshot.
- `evidence/private-infra-validation.sanitized.json` - machine-readable private
  infrastructure validation evidence snapshot.
- `evidence/private-infra-remediation-plan.sanitized.json` - machine-readable
  private infrastructure remediation plan evidence snapshot.
- `evidence/private-infra-remediation-execution.sanitized.json` - machine-readable
  private infrastructure remediation execution evidence snapshot.
- `evidence/private-infra-post-remediation-drift-refresh.sanitized.json` -
  machine-readable post-remediation drift refresh evidence snapshot.
- `evidence/private-infra-scheduled-validation.sanitized.json` -
  machine-readable recurring scheduled validation evidence snapshot.
- `evidence/private-infra-scheduled-alerting.sanitized.json` -
  machine-readable scheduled validation alerting evidence snapshot.
- `evidence/platform-maturity-70.sanitized.json` - machine-readable 70
  percent DevOps/platform milestone evidence snapshot.
- `evidence/gitops-layout.sanitized.json` - machine-readable GitOps layout
  evidence snapshot.
- `evidence/gitops-promotion-drift.sanitized.json` - machine-readable GitOps
  image promotion and drift evidence snapshot.
- `evidence/gitops-drift-remediation.sanitized.json` - machine-readable GitOps
  drift remediation evidence snapshot.
- `evidence/gitops-image-automation.sanitized.json` - machine-readable GitOps
  image automation evidence snapshot.
- `evidence/observability-proof.sanitized.json` - machine-readable public-safe
  observability evidence snapshot.
- `evidence/alert-routing.sanitized.json` - machine-readable public-safe alert
  routing evidence snapshot.
- `evidence/public-evidence-index.sanitized.json` - machine-readable public
  evidence index.
- `assets/drivedesk-core-demo-overview.png` - public demo screenshot.

The public repository export also generates:

- `docs/openapi.json` - FastAPI OpenAPI schema from the exported API.
- `apps/admin/public-demo/index.html` - static fake-data product demo shell.
- `GET /demo/public` - read-only synthetic demo payload in the exported API.
- `incidentResponse` - public-safe incident response contract in the demo
  payload and Incidents tab.
- `GET /business-record-lifecycle-policies` - public-safe lifecycle policy catalog.
- `POST /tenants/{tenant_id}/integration-exports/accounting` - public-safe
  outbound accounting export contract in the exported API.
- `POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks` -
  public-safe connection diagnostics contract in the exported API.
- `POST /tenants/{tenant_id}/integration-reconciliations` - public-safe
  provider evidence reconciliation contract in the exported API.
- `POST /tenants/{tenant_id}/integration-incidents` - public-safe incident
  runbook creation contract in the exported API.
- `GET /tenants/{tenant_id}/integration-operator-review` - public-safe
  integration failure review contract in the exported API.
- `workflow`, `timeline`, and `domainEvents` - synthetic workflow contract in
  the public demo payload.
- `scripts/run_public_demo_local.sh` - one-command local API run.
- `scripts/check_public_demo_api.sh` - local API contract and client-example smoke.
- `scripts/check_public_backup_restore.sh` - public-safe synthetic recovery drill.
- `scripts/check_public_release_rollback.sh` - public-safe release rollback drill.
- `scripts/check_public_slo_canary_gate.sh` - public-safe SLO canary gate drill.
- `scripts/check_public_staged_promotion.sh` - public-safe staged promotion drill.
- `scripts/check_public_helm_render.sh` - public-safe Helm chart validation.
- `scripts/check_public_opentofu_plan.sh` - public-safe OpenTofu plan validation.
- `scripts/check_public_infra_state_drift.sh` - public-safe infrastructure state drift validation.
- `scripts/check_public_runtime_rollout.sh` - public-safe private staging runtime rollout validation.
- `scripts/check_public_private_infra_validation.sh` - public-safe private infrastructure validation.
- `scripts/check_public_private_infra_remediation.sh` - public-safe private infrastructure remediation plan validation.
- `scripts/check_public_private_infra_remediation_execution.sh` - public-safe private infrastructure remediation execution validation.
- `scripts/check_public_private_infra_post_remediation_drift_refresh.sh` - public-safe post-remediation drift refresh validation.
- `scripts/check_public_private_infra_scheduled_validation.sh` - public-safe recurring scheduled validation.
- `scripts/check_public_private_infra_scheduled_alerting.sh` - public-safe scheduled validation alerting.
- `scripts/check_public_platform_maturity_70.sh` - public-safe 70 percent milestone validation.
- `scripts/check_public_reviewer_quickstart.sh` - public-safe reviewer quickstart validation.
- `scripts/check_public_project_status.sh` - public-safe project status validation.
- `scripts/check_public_technical_capability_map.sh` - public-safe capability map validation.
- `scripts/check_public_observability_proof.sh` - public-safe observability proof validation.
- `scripts/check_public_alert_routing.sh` - public-safe alert routing validation.
- `scripts/check_public_engineering_proof.sh` - public-safe proof tab and evidence contract validation.
- `scripts/check_public_evidence_index.sh` - public-safe evidence index validation.
- `scripts/check_public_gitops_layout.sh` - public-safe GitOps layout validation.
- `scripts/check_public_gitops_image_automation.sh` - public-safe GitOps image automation validation.
- `scripts/check_public_gitops_promotion_drift.sh` - public-safe GitOps promotion and drift validation.
- `scripts/check_public_gitops_drift_remediation.sh` - public-safe GitOps drift remediation validation.
- `scripts/generate_public_demo_sdk.py` - generated SDK builder from OpenAPI.
- `scripts/check_public_demo_sdk.sh` - generated SDK drift and runtime smoke.
- `sdk/generated/public-demo/` - generated Python, JavaScript, and TypeScript
  client artifacts.
- `examples/curl/demo-public.sh` - curl client example.
- `examples/python/demo_public_client.py` - Python client example.
- `examples/python/demo_adapter_operation_plan.py` - Python adapter operation plan SDK example.
- `examples/js/demo-public-fetch.js` - JavaScript fetch client example.
- `examples/js/demo-adapter-operation-plan.mjs` - JavaScript adapter operation plan SDK example.
- `PUBLIC_EXPORT_MANIFEST.md` - file list and export boundary summary.

Hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

## Verification Path

1. Start with `REVIEWER_QUICKSTART.md`.
2. Open the hosted demo and switch to the Proof tab.
3. Inspect `docs/openapi.json`.
4. Run `bash scripts/ci_smoke_public.sh`.
5. Run `bash scripts/check_public_engineering_proof.sh`.
6. Run `bash scripts/check_public_demo_api.sh`.
7. Run one generated client example from `examples/`.
8. Review `PROJECT_STATUS.md`, `TECHNICAL_CAPABILITY_MAP.md`, `EVIDENCE_INDEX.md`, `OBSERVABILITY_PROOF.md`, `ALERT_ROUTING_EVIDENCE.md`, `INCIDENT_RESPONSE_DEMO.md`, `ENGINEERING_PROOF.md`, `PLATFORM_MATURITY_70.md`, and `SANITIZED_EVIDENCE.md`.
9. Review `SYSTEM_DESIGN.md`, `GITOPS_DELIVERY.md`, and the recovery evidence docs.

## Engineering Summary

The private repository keeps building the product. This folder is the public
engineering surface: demo, API contract, generated clients, architecture docs,
sanitized evidence, and repeatable validation gates.

The export release gate makes this repeatable. Instead of manually copying
files, the private source builds a fresh public package, validates the schema,
runs public smoke checks, validates the demo shell, and leaves the result ready
for a separate public repository.
