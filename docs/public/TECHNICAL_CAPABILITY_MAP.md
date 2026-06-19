# Technical Capability Map

This map connects the current DriveDesk Core capabilities to their public-safe
implementation surface, evidence, and verifier commands.

## Capability Matrix

| Capability | Implementation surface | Evidence | Verifier |
| --- | --- | --- | --- |
| Public engineering entrypoint | GitHub Pages root `index.html`, compact system review path, quickstart, and static demo shell | `docs/public/SYSTEM_REVIEW_PATH.md`, `docs/public/REVIEWER_QUICKSTART.md`, `docs/public/ENGINEERING_REVIEW_GUIDE.md`, `docs/public/ENGINEERING_PROOF.md` | `bash scripts/check_public_pages_entrypoint.sh && bash scripts/check_public_system_review_path.sh && bash scripts/check_public_reviewer_quickstart.sh` |
| Platform tour | Business event -> workflow -> adapter -> incident -> proof route across Control Tower, Adapter Studio, operations, and proof | `docs/public/PLATFORM_TOUR.md`, `apps/admin/public-demo/index.html`, `GET /demo/public` | `bash scripts/check_public_platform_tour.sh && bash scripts/check_public_demo_api.sh` |
| Project status | Current public-safe state, limits, next work, and validation commands | `docs/public/PROJECT_STATUS.md`, `docs/public/ROADMAP.md` | `bash scripts/check_public_project_status.sh` |
| Read-only API contract | FastAPI `GET /demo/public`, `GET /demo/connector-fixture-replay`, and generated `docs/openapi.json` | `docs/public/API_BACKED_DEMO.md`, `examples/curl/demo-public.sh` | `bash scripts/check_public_demo_api.sh` |
| Generated client SDK | Python, JavaScript, and TypeScript demo clients plus typed file-import, CRM provider-intake, and worker-backed adapter operation plans, standalone connector replay validation, and Adapter Studio validation | `docs/public/CLIENT_SDK.md`, `docs/public/ADAPTER_DEVELOPER_GUIDE.md`, `sdk/generated/public-demo/`, `examples/python/demo_adapter_operation_plan.py`, `examples/js/demo-adapter-operation-plan.mjs` | `bash scripts/check_public_demo_sdk.sh && bash scripts/check_public_adapter_developer_guide.sh` |
| Auth, RBAC, and tenant boundary | Bearer-token auth, tenant-scoped helpers, platform-admin model | `docs/public/AUTH_FOUNDATION.md`, `docs/public/TENANT_ISOLATION.md`, `docs/public/PLATFORM_ADMIN.md` | `bash scripts/ci_smoke_public.sh` |
| Audit and outbox recovery | Audited retry path for failed outbox jobs | `docs/public/OUTBOX_RECOVERY.md`, `docs/adr/0030-outbox-retry-recovery.md` | `bash scripts/ci_smoke_public.sh` |
| Business records and workflow automation | Tenant-owned records, lifecycle transitions, reusable workflow scenarios, end-to-end workflow-to-proof scenario, workflow rules, action runs | `docs/public/BUSINESS_RECORDS.md`, `docs/public/BUSINESS_RECORD_LIFECYCLE.md`, `docs/public/WORKFLOW_RULES.md`, `docs/public/WORKFLOW_ACTION_RUNS.md`, `docs/public/WORKFLOW_DEMO.md` | `bash scripts/ci_smoke_public.sh && bash scripts/check_public_demo_api.sh` |
| Business operations control tower | Provider intake preview, CRM runtime adapter contract, tenant-owned state observations, role-specific workbench context preview, automatic detection preview, escalation preview with owner/queue/SLA routing, action-plan preview with ordered operator work, notification preview with channel/draft boundaries, business exceptions, role briefing preview, approval-gated repair actions, dry-run execution, aggregate metrics, and public demo contract | `docs/public/BUSINESS_CONTROL_TOWER.md`, `GET /demo/public`, `POST /tenants/{tenant_id}/business-provider-intake/preview`, `POST /tenants/{tenant_id}/business-workbench-context/preview`, `POST /tenants/{tenant_id}/business-detections/preview`, `POST /tenants/{tenant_id}/business-escalations/preview`, `POST /tenants/{tenant_id}/business-action-plans/preview`, `POST /tenants/{tenant_id}/business-notifications/preview`, `POST /tenants/{tenant_id}/business-briefings/preview`, `apps/admin/public-demo/index.html` | `bash scripts/check_public_business_control_tower.sh && bash scripts/check_public_demo_api.sh` |
| Integration adapter model | Runtime adapter catalog, public-safe provider connector guide, connector certification path, connector fixture replay, `GET /demo/connector-fixture-replay`, Adapter Studio, adapter developer guide, CRM deal intake adapter, auth profiles, secret boundaries, operation scenarios, typed SDK operation plans, mapping preview, scopes, diagnostics, reconciliation, incident cards | `apps/admin/public-demo/index.html`, `docs/public/PROVIDER_CONNECTOR_GUIDE.md`, `docs/public/CONNECTOR_CERTIFICATION.md`, `docs/public/CONNECTOR_FIXTURE_REPLAY.md`, `docs/public/ADAPTER_DEVELOPER_GUIDE.md`, `docs/public/INTEGRATION_ADAPTER_CATALOG.md`, `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`, `docs/public/INTEGRATION_RECONCILIATION.md`, `docs/public/CLIENT_SDK.md`, `docs/public/evidence/connector-certification.sanitized.json`, `docs/public/evidence/connector-fixture-replay.sanitized.json`, `examples/connector-fixtures/replay-fixtures.sanitized.json`, `docs/adr/0072-mock-crm-deal-adapter.md`, `docs/adr/0073-adapter-auth-profile-boundary.md`, `docs/adr/0074-public-safe-connector-certification.md`, `docs/adr/0075-public-safe-connector-fixture-replay.md` | `bash scripts/check_public_provider_connector_guide.sh && bash scripts/check_public_connector_certification.sh && bash scripts/check_public_connector_fixture_replay.sh && bash scripts/check_public_adapter_developer_guide.sh && bash scripts/check_public_demo_api.sh && bash scripts/check_public_demo_sdk.sh` |
| Recovery drills | Synthetic backup/restore, rollback, canary gate, and staged promotion evidence | `docs/public/BACKUP_RESTORE_EVIDENCE.md`, `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` | `bash scripts/check_public_backup_restore.sh && bash scripts/check_public_release_rollback.sh && bash scripts/check_public_slo_canary_gate.sh && bash scripts/check_public_staged_promotion.sh` |
| Observability proof | Metrics, structured logs, alert rules, runbooks, and dashboard panels represented as public-safe evidence | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/evidence/observability-proof.sanitized.json` | `bash scripts/check_public_observability_proof.sh` |
| Alert routing | Demo Operations tab, `GET /demo/public` `alertRouting` payload, Alertmanager-style route tree, receivers, dedupe keys, escalation, silences, runbook bindings, and failure artifacts | `apps/admin/public-demo/index.html`, `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/evidence/alert-routing.sanitized.json` | `bash scripts/check_public_alert_routing.sh && bash scripts/check_public_demo_api.sh` |
| Incident response | Demo Incidents tab, `GET /demo/public` `incidentResponse` payload, incident queue, owner assignment, recovery timeline, mitigation actions, and resolution evidence | `apps/admin/public-demo/index.html`, `docs/public/INCIDENT_RESPONSE_DEMO.md`, `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md` | `bash scripts/check_public_demo_api.sh && bash scripts/check_public_engineering_proof.sh` |
| GitOps delivery | Helm chart, Argo CD layout, image automation, drift and remediation evidence | `docs/public/HELM_CHART.md`, `docs/public/GITOPS_DELIVERY.md`, `docs/public/GITOPS_IMAGE_AUTOMATION.md`, `docs/public/GITOPS_DRIFT_REMEDIATION.md` | `bash scripts/check_public_helm_render.sh && bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_gitops_image_automation.sh` |
| OpenTofu and infra drift | Public-safe plan summary, state drift, runtime rollout, scheduled validation and alerting | `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md`, `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md` | `bash scripts/check_public_opentofu_plan.sh && bash scripts/check_public_infra_state_drift.sh && bash scripts/check_public_private_infra_scheduled_validation.sh && bash scripts/check_public_private_infra_scheduled_alerting.sh` |
| Sanitized evidence boundary | Public-safe evidence files with no raw logs, credentials, hostnames, addresses, or production data | `docs/public/SANITIZED_EVIDENCE.md`, `docs/public/evidence/*.sanitized.json`, `PUBLIC_EXPORT_MANIFEST.md` | `bash scripts/check_public_export_secrets.sh` |
| Evidence index | Machine-readable mapping from public capabilities to docs, evidence files, verifier commands, public URLs, and boundary notes | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json` | `bash scripts/check_public_evidence_index.sh` |
| Engineering proof contract | Demo Proof tab, API payload, OpenAPI schema, SDK artifacts, docs, and CI gates | `docs/public/ENGINEERING_PROOF.md`, `docs/public/evidence/platform-maturity-70.sanitized.json` | `bash scripts/check_public_engineering_proof.sh` |

## Review Order

1. Open `docs/public/SYSTEM_REVIEW_PATH.md`.
2. Open `docs/public/PLATFORM_TOUR.md`.
3. Open `docs/public/REVIEWER_QUICKSTART.md`.
4. Open the GitHub Pages engineering reference.
5. Open the live demo and switch to the Workflow, Control Tower, Integrations, Operations, Incidents, and Proof tabs.
6. Read `docs/public/PROJECT_STATUS.md`.
7. Inspect `docs/openapi.json`, `GET /demo/public`, and `GET /demo/connector-fixture-replay`.
8. Run `bash scripts/ci_smoke_public.sh`.
9. Run `bash scripts/check_public_system_review_path.sh`.
10. Run `bash scripts/check_public_platform_tour.sh`.
11. Run `bash scripts/check_public_reviewer_quickstart.sh`.
12. Run `bash scripts/check_public_project_status.sh`.
13. Run `bash scripts/check_public_technical_capability_map.sh`.
14. Run `bash scripts/check_public_evidence_index.sh`.
15. Run `bash scripts/check_public_business_control_tower.sh`.
16. Run `bash scripts/check_public_observability_proof.sh`.
17. Run `bash scripts/check_public_alert_routing.sh`.
18. Run `bash scripts/check_public_connector_certification.sh`.
19. Run `bash scripts/check_public_connector_fixture_replay.sh`.
20. Run the capability-specific verifier from the table above.

## Boundary

The public surface uses synthetic data and sanitized evidence. It does not expose
private runtime addresses, credentials, raw logs, production data, private state,
or customer-specific operational history.
