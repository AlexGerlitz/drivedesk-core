# Public Verification Matrix

This matrix is the compact proof route for DriveDesk Core. It maps each public
engineering claim to the artifact, verifier command, and pass signal that prove
the current state.

## Matrix

| Claim | Evidence | Verifier | Pass signal |
| --- | --- | --- | --- |
| One-command public review path is connected | `docs/public/PUBLIC_REVIEW_BUNDLE.md`, `docs/public/evidence/public-review-bundle.sanitized.json`, `scripts/run_public_review_bundle.sh` | `bash scripts/check_public_review_bundle.sh` | The bundle command, included checks, review docs, evidence index entry, public smoke, export, README, and Pages links stay wired together. |
| Public entrypoint is navigable | `index.html`, `docs/public/SYSTEM_REVIEW_PATH.md`, `docs/public/REVIEWER_QUICKSTART.md` | `bash scripts/check_public_pages_entrypoint.sh && bash scripts/check_public_system_review_path.sh && bash scripts/check_public_reviewer_quickstart.sh` | Pages root links demo, system path, quickstart, status, capability map, evidence index, and OpenAPI. |
| Demo health is live-verifiable | `docs/public/PUBLIC_DEMO_HEALTH.md`, `docs/public/evidence/public-demo-health.sanitized.json`, `.github/workflows/public-demo-health.yml` | `bash scripts/check_public_demo_health.sh` | Demo shell, static data, OpenAPI, generated SDK manifest, and workflow contract are connected. |
| OpenAPI contract is not stale | `docs/public/OPENAPI_DRIFT.md`, `docs/public/evidence/openapi-drift.sanitized.json`, `docs/openapi.json` | `bash scripts/check_public_openapi_drift.sh` | Committed schema matches generated FastAPI schema, SDK manifest, and demo operation markers. |
| Generated SDK matches the API | `docs/public/CLIENT_SDK.md`, `sdk/generated/public-demo/`, `examples/python/demo_public_client.py`, `examples/js/demo-public-fetch.js` | `bash scripts/check_public_demo_sdk.sh` | Python, JavaScript, TypeScript, and adapter-operation examples validate against the generated OpenAPI manifest. |
| Business OS route is connected | `docs/public/PLATFORM_TOUR.md`, `docs/public/API_BACKED_DEMO.md`, `GET /demo/public` | `bash scripts/check_public_platform_tour.sh && bash scripts/check_public_demo_api.sh` | Business event -> workflow -> adapter -> incident -> proof is visible through docs, demo payload, and UI tabs. |
| Control Tower workflow is executable as a safe preview | `docs/public/BUSINESS_CONTROL_TOWER.md`, `docs/public/BUSINESS_INTAKE_PIPELINE.md`, `docs/public/BUSINESS_TASK_HANDOFF.md`, `docs/public/BUSINESS_NOTIFICATION_CHANNELS.md` | `bash scripts/check_public_business_control_tower.sh && bash scripts/check_public_business_intake_pipeline.sh && bash scripts/check_public_business_task_handoff.sh && bash scripts/check_public_business_notification_channels.sh` | Provider signals become safe observations, task cards, draft notifications, and operator context without external writes. |
| Action execution is gated and auditable | `docs/public/BUSINESS_ACTION_EXECUTION.md`, `docs/public/BUSINESS_APPROVAL_GATEWAY.md` | `bash scripts/check_public_business_action_execution.sh && bash scripts/check_public_business_approval_gateway.sh` | Execution candidates carry idempotency keys, preflight checks, dry-run results, approval gates, and audit evidence. |
| Integration runtime and repair paths are connected | `docs/public/INTEGRATION_RUNTIME.md`, `docs/public/INTEGRATION_EXECUTION.md`, `docs/public/INTEGRATION_REPAIR.md`, `docs/public/evidence/integration-repair.sanitized.json` | `bash scripts/check_public_integration_runtime.sh && bash scripts/check_public_integration_execution.sh && bash scripts/check_public_integration_repair.sh` | Runtime plan, execution ledger, retry/dead-letter path, runbook action, and postcheck evidence validate together. |
| Notification delivery has retry and review evidence | `docs/public/NOTIFICATION_DELIVERY.md`, `docs/public/evidence/notification-delivery.sanitized.json` | `bash scripts/check_public_notification_delivery.sh` | Draft notification, outbox, worker dispatch, provider gate, retry, dead-letter, operator review, and metrics are present. |
| Observability and alert routing are reviewable | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/OBSERVABILITY_DASHBOARD.md`, `docs/public/ALERT_ROUTING_EVIDENCE.md` | `bash scripts/check_public_observability_proof.sh && bash scripts/check_public_observability_dashboard.sh && bash scripts/check_public_alert_routing.sh` | Metrics, log lines, alert rules, dashboard panels, receivers, silences, dedupe keys, and runbook links validate. |
| Incident and repair surfaces close the loop | `docs/public/INCIDENT_RESPONSE_DEMO.md`, `docs/public/ENGINEERING_PROOF.md`, `apps/admin/public-demo/index.html` | `bash scripts/check_public_engineering_proof.sh && bash scripts/check_public_demo_api.sh` | Incidents link to owner, timeline, mitigation, recovery, resolution evidence, and proof payload. |
| Release safety is covered by drills | `docs/public/BACKUP_RESTORE_EVIDENCE.md`, `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` | `bash scripts/check_public_backup_restore.sh && bash scripts/check_public_release_rollback.sh && bash scripts/check_public_slo_canary_gate.sh && bash scripts/check_public_staged_promotion.sh` | Backup restore, rollback, failed canary block, and staged promotion evidence validate without production data. |
| GitOps and infrastructure contracts are reviewable | `docs/public/HELM_CHART.md`, `docs/public/GITOPS_DELIVERY.md`, `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` | `bash scripts/check_public_helm_render.sh && bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh && bash scripts/check_public_infra_state_drift.sh` | Helm templates, Argo CD layout, plan-only OpenTofu summary, and desired-vs-observed drift evidence validate. |
| Private runtime evidence stays sanitized | `docs/public/RUNTIME_ROLLOUT_EVIDENCE.md`, `docs/public/PRIVATE_INFRA_VALIDATION.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md` | `bash scripts/check_public_runtime_rollout.sh && bash scripts/check_public_private_infra_validation.sh && bash scripts/check_public_private_infra_scheduled_validation.sh && bash scripts/check_public_private_infra_scheduled_alerting.sh` | Runtime rollout, validation, recurring schedule, and alerting evidence expose only sanitized summaries. |
| Evidence index and export boundary stay consistent | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json`, `docs/public/SANITIZED_EVIDENCE.md`, `PUBLIC_EXPORT_MANIFEST.md` | `bash scripts/check_public_evidence_index.sh && bash scripts/check_public_export_secrets.sh` | Every indexed document, evidence file, verifier command, URL, and boundary validates; public export secret scan passes. |

## Full Smoke

```bash
bash scripts/ci_smoke_public.sh
```

## Self-Check

```bash
bash scripts/check_public_verification_matrix.sh
```

## Boundary

This matrix references public-safe documents, synthetic data, sanitized evidence,
and verifier commands only. It does not require production data, credentials,
private runtime addresses, raw logs, customer records, or private deployment
state.
