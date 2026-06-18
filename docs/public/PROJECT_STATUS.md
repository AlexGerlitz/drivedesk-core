# Project Status

This document is the current public-safe status snapshot for DriveDesk Core. It
separates validated engineering surface, synthetic evidence, and planned product
work so the repository can be reviewed without private operational context.

## Snapshot

| Area | Current state | Evidence | Verification |
| --- | --- | --- | --- |
| Public entrypoint | GitHub Pages root review hub is generated from the private export pipeline. | `index.html`, `docs/public/ENGINEERING_REVIEW_GUIDE.md` | `bash scripts/check_public_pages_entrypoint.sh` |
| API contract | Read-only synthetic demo API and generated OpenAPI schema are present. | `docs/openapi.json`, `GET /demo/public`, `docs/public/API_BACKED_DEMO.md` | `bash scripts/check_public_demo_api.sh` |
| Client SDK | Python, JavaScript, and TypeScript demo clients are generated from OpenAPI. | `docs/public/CLIENT_SDK.md`, `sdk/generated/public-demo/` | `bash scripts/check_public_demo_sdk.sh` |
| Auth and tenant boundary | Public-safe auth, RBAC, platform-admin, and tenant-isolation contracts are documented and tested. | `docs/public/AUTH_FOUNDATION.md`, `docs/public/TENANT_ISOLATION.md`, `docs/public/PLATFORM_ADMIN.md` | `bash scripts/ci_smoke_public.sh` |
| Business workflow | Tenant-owned business records, lifecycle transitions, workflow rules, action runs, audit, and outbox handoff are covered. | `docs/public/BUSINESS_RECORDS.md`, `docs/public/WORKFLOW_RULES.md`, `docs/public/WORKFLOW_ACTION_RUNS.md` | `bash scripts/ci_smoke_public.sh` |
| Integration hub | Adapter catalog, mapping, scopes, operation contracts, diagnostics, reconciliation, incident cards, and operator review are represented with public-safe providers. | `docs/public/INTEGRATION_ADAPTER_CATALOG.md`, `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`, `docs/public/INTEGRATION_RECONCILIATION.md` | `bash scripts/check_public_demo_api.sh` |
| Recovery and release safety | Backup/restore, rollback, SLO canary gate, and staged promotion drills use sanitized synthetic evidence. | `docs/public/BACKUP_RESTORE_EVIDENCE.md`, `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` | `bash scripts/check_public_backup_restore.sh && bash scripts/check_public_release_rollback.sh && bash scripts/check_public_slo_canary_gate.sh && bash scripts/check_public_staged_promotion.sh` |
| GitOps and IaC | Helm, Argo CD, OpenTofu, image automation, drift detection, and remediation are modeled with public-safe manifests and evidence. | `docs/public/GITOPS_DELIVERY.md`, `docs/public/GITOPS_IMAGE_AUTOMATION.md`, `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` | `bash scripts/check_public_helm_render.sh && bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh && bash scripts/check_public_infra_state_drift.sh` |
| Evidence boundary | Public export contains synthetic data and sanitized evidence only. | `PUBLIC_EXPORT_MANIFEST.md`, `docs/public/SANITIZED_EVIDENCE.md`, `docs/public/evidence/*.sanitized.json` | `bash scripts/check_public_export_secrets.sh` |
| Capability map | Each visible capability is linked to implementation surface, evidence, and verifier command. | `docs/public/TECHNICAL_CAPABILITY_MAP.md` | `bash scripts/check_public_technical_capability_map.sh` |
| Observability proof | Metrics, structured logs, alerts, runbooks, and dashboard panels are represented with public-safe synthetic evidence. | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/evidence/observability-proof.sanitized.json` | `bash scripts/check_public_observability_proof.sh` |
| Alert routing | Alertmanager-style routes, receivers, dedupe keys, escalation, silences, and runbook bindings are represented with public-safe synthetic evidence. | `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/evidence/alert-routing.sanitized.json` | `bash scripts/check_public_alert_routing.sh` |

## Current Limits

- The public repository is a sanitized engineering surface, not the private
  product source.
- Public evidence uses synthetic data and public-safe manifests.
- The hosted demo is static-first through GitHub Pages; the API contract can be
  run locally with `bash scripts/run_public_demo_local.sh`.
- Real customer data, private infrastructure addresses, credentials, raw logs,
  payment provider details, and production deployment state are not included.
- Mobile apps, commercial onboarding, and real external-provider adapters are
  outside the current public surface.

## Next Engineering Work

Longer public-safe direction lives in `docs/public/ROADMAP.md`.

1. Add richer workflow examples that reuse the same rule, action-run, task,
   event, audit, and outbox shape.
2. Add more adapter SDK examples with mapping, preview, execution, retry, and
   operator review paths.
3. Expand the public observability proof into richer synthetic dashboard
   examples.
4. Deepen the admin frontend shell around the existing API and public demo
   contract.
5. Keep public and private repositories separated through the export gate and
   secret boundary checks.

## Verification

```bash
bash scripts/ci_smoke_public.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_export_secrets.sh
```
