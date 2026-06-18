# Technical Capability Map

This map connects the current DriveDesk Core capabilities to their public-safe
implementation surface, evidence, and verifier commands.

## Capability Matrix

| Capability | Implementation surface | Evidence | Verifier |
| --- | --- | --- | --- |
| Public review entrypoint | GitHub Pages root `index.html` and static demo shell | `docs/public/ENGINEERING_REVIEW_GUIDE.md`, `docs/public/ENGINEERING_PROOF.md` | `bash scripts/check_public_pages_entrypoint.sh` |
| Project status | Current public-safe state, limits, next work, and validation commands | `docs/public/PROJECT_STATUS.md`, `docs/public/ROADMAP.md` | `bash scripts/check_public_project_status.sh` |
| Read-only API contract | FastAPI `GET /demo/public` and generated `docs/openapi.json` | `docs/public/API_BACKED_DEMO.md`, `examples/curl/demo-public.sh` | `bash scripts/check_public_demo_api.sh` |
| Generated client SDK | Python, JavaScript, and TypeScript demo clients | `docs/public/CLIENT_SDK.md`, `sdk/generated/public-demo/` | `bash scripts/check_public_demo_sdk.sh` |
| Auth, RBAC, and tenant boundary | Bearer-token auth, tenant-scoped helpers, platform-admin model | `docs/public/AUTH_FOUNDATION.md`, `docs/public/TENANT_ISOLATION.md`, `docs/public/PLATFORM_ADMIN.md` | `bash scripts/ci_smoke_public.sh` |
| Audit and outbox recovery | Audited retry path for failed outbox jobs | `docs/public/OUTBOX_RECOVERY.md`, `docs/adr/0030-outbox-retry-recovery.md` | `bash scripts/ci_smoke_public.sh` |
| Business records and workflow automation | Tenant-owned records, lifecycle transitions, workflow rules, action runs | `docs/public/BUSINESS_RECORDS.md`, `docs/public/BUSINESS_RECORD_LIFECYCLE.md`, `docs/public/WORKFLOW_RULES.md`, `docs/public/WORKFLOW_ACTION_RUNS.md` | `bash scripts/ci_smoke_public.sh` |
| Integration adapter model | Runtime adapter catalog, mapping preview, scopes, diagnostics, reconciliation, incident cards | `docs/public/INTEGRATION_ADAPTER_CATALOG.md`, `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`, `docs/public/INTEGRATION_RECONCILIATION.md` | `bash scripts/check_public_demo_api.sh` |
| Recovery drills | Synthetic backup/restore, rollback, canary gate, and staged promotion evidence | `docs/public/BACKUP_RESTORE_EVIDENCE.md`, `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` | `bash scripts/check_public_backup_restore.sh && bash scripts/check_public_release_rollback.sh && bash scripts/check_public_slo_canary_gate.sh && bash scripts/check_public_staged_promotion.sh` |
| Observability proof | Metrics, structured logs, alert rules, runbooks, and dashboard panels represented as public-safe evidence | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/evidence/observability-proof.sanitized.json` | `bash scripts/check_public_observability_proof.sh` |
| Alert routing | Alertmanager-style route tree, receivers, dedupe keys, escalation, silences, runbook bindings, and failure artifacts | `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/evidence/alert-routing.sanitized.json` | `bash scripts/check_public_alert_routing.sh` |
| GitOps delivery | Helm chart, Argo CD layout, image automation, drift and remediation evidence | `docs/public/HELM_CHART.md`, `docs/public/GITOPS_DELIVERY.md`, `docs/public/GITOPS_IMAGE_AUTOMATION.md`, `docs/public/GITOPS_DRIFT_REMEDIATION.md` | `bash scripts/check_public_helm_render.sh && bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_gitops_image_automation.sh` |
| OpenTofu and infra drift | Public-safe plan summary, state drift, runtime rollout, scheduled validation and alerting | `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md` | `bash scripts/check_public_opentofu_plan.sh && bash scripts/check_public_infra_state_drift.sh && bash scripts/check_public_private_infra_scheduled_validation.sh && bash scripts/check_public_private_infra_scheduled_alerting.sh` |
| Sanitized evidence boundary | Public-safe evidence files with no raw logs, credentials, hostnames, addresses, or production data | `docs/public/SANITIZED_EVIDENCE.md`, `docs/public/evidence/*.sanitized.json`, `PUBLIC_EXPORT_MANIFEST.md` | `bash scripts/check_public_export_secrets.sh` |
| Engineering proof contract | Demo Proof tab, API payload, OpenAPI schema, SDK artifacts, docs, and CI gates | `docs/public/ENGINEERING_PROOF.md`, `docs/public/evidence/portfolio-70-milestone.sanitized.json` | `bash scripts/check_public_engineering_proof.sh` |

## Review Order

1. Open the GitHub Pages root review hub.
2. Open the live demo and switch to the Proof tab.
3. Read `docs/public/PROJECT_STATUS.md`.
4. Inspect `docs/openapi.json` and `GET /demo/public`.
5. Run `bash scripts/ci_smoke_public.sh`.
6. Run `bash scripts/check_public_project_status.sh`.
7. Run `bash scripts/check_public_technical_capability_map.sh`.
8. Run `bash scripts/check_public_observability_proof.sh`.
9. Run `bash scripts/check_public_alert_routing.sh`.
10. Run the capability-specific verifier from the table above.

## Boundary

The public surface uses synthetic data and sanitized evidence. It does not expose
private runtime addresses, credentials, raw logs, production data, private state,
or customer-specific operational history.
