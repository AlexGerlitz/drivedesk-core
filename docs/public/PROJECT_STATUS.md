# Project Status

This document is the current public-safe status snapshot for DriveDesk Core. It
separates validated engineering surface, synthetic evidence, and planned product
work so the repository can be verified without private operational context.

## Snapshot

| Area | Current state | Evidence | Verification |
| --- | --- | --- | --- |
| Public entrypoint | GitHub Pages engineering reference, compact system review path, and quickstart are generated from the private export pipeline. | `index.html`, `docs/public/SYSTEM_REVIEW_PATH.md`, `docs/public/REVIEWER_QUICKSTART.md`, `docs/public/ENGINEERING_REVIEW_GUIDE.md` | `bash scripts/check_public_pages_entrypoint.sh && bash scripts/check_public_system_review_path.sh && bash scripts/check_public_reviewer_quickstart.sh` |
| Platform tour | Business event, Control Tower, workflow, Adapter Studio, outbox, incidents, and proof are connected into one product path. | `docs/public/PLATFORM_TOUR.md`, `apps/admin/public-demo/index.html`, `GET /demo/public` | `bash scripts/check_public_platform_tour.sh && bash scripts/check_public_demo_api.sh` |
| API contract | Read-only synthetic demo API, standalone connector replay API, standalone business intake pipeline API, standalone business task handoff API, standalone notification channel matrix API, standalone Business Context Assistant API, standalone business action execution API, standalone business approval gateway API, standalone integration runtime API, standalone integration execution API, standalone business scenario replay API, and generated OpenAPI schema are present. | `docs/openapi.json`, `GET /demo/public`, `GET /demo/connector-fixture-replay`, `GET /demo/business-intake-pipeline`, `GET /demo/business-task-handoff`, `GET /demo/business-notification-channels`, `GET /demo/business-context-assistant`, `GET /demo/business-action-execution`, `GET /demo/business-approval-gateway`, `GET /demo/integration-runtime`, `GET /demo/integration-execution`, `GET /demo/business-scenario-replay`, `docs/public/API_BACKED_DEMO.md` | `bash scripts/check_public_demo_api.sh && bash scripts/check_public_business_intake_pipeline.sh && bash scripts/check_public_business_task_handoff.sh && bash scripts/check_public_business_notification_channels.sh && bash scripts/check_public_business_context_assistant.sh && bash scripts/check_public_business_action_execution.sh && bash scripts/check_public_business_approval_gateway.sh && bash scripts/check_public_integration_runtime.sh && bash scripts/check_public_integration_execution.sh && bash scripts/check_public_business_scenario_replay.sh` |
| Client SDK | Python, JavaScript, and TypeScript demo clients are generated from OpenAPI, including typed file-import and Bitrix-style CRM adapter operation helpers, standalone connector replay validation, Adapter Studio workbench contract, integration runtime metadata, and integration execution metadata. | `docs/public/CLIENT_SDK.md`, `docs/public/ADAPTER_DEVELOPER_GUIDE.md`, `docs/public/INTEGRATION_RUNTIME.md`, `docs/public/INTEGRATION_EXECUTION.md`, `sdk/generated/public-demo/`, `examples/python/demo_adapter_operation_plan.py`, `examples/js/demo-adapter-operation-plan.mjs` | `bash scripts/check_public_demo_sdk.sh && bash scripts/check_public_adapter_developer_guide.sh && bash scripts/check_public_integration_runtime.sh && bash scripts/check_public_integration_execution.sh` |
| Auth and tenant boundary | Public-safe auth, RBAC, platform-admin, and tenant-isolation contracts are documented and tested. | `docs/public/AUTH_FOUNDATION.md`, `docs/public/TENANT_ISOLATION.md`, `docs/public/PLATFORM_ADMIN.md` | `bash scripts/ci_smoke_public.sh` |
| Business workflow | Tenant-owned business records, lifecycle transitions, reusable workflow scenarios, end-to-end workflow-to-proof scenario, workflow rules, action runs, audit, and outbox handoff are covered. | `docs/public/BUSINESS_RECORDS.md`, `docs/public/WORKFLOW_RULES.md`, `docs/public/WORKFLOW_ACTION_RUNS.md`, `docs/public/WORKFLOW_DEMO.md` | `bash scripts/ci_smoke_public.sh && bash scripts/check_public_demo_api.sh` |
| Business control tower | Provider intake preview, cross-system observations, role-specific workbench context preview, automatic detection preview, escalation preview with owner/queue/SLA routing, action-plan preview with ordered operator work, notification preview with channel/draft boundaries, business exception queue, role briefing preview, approval-gated repair action, dry-run execution, aggregate metrics, and public demo payload are covered. | `docs/public/BUSINESS_CONTROL_TOWER.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `POST /tenants/{tenant_id}/business-provider-intake/preview`, `POST /tenants/{tenant_id}/business-workbench-context/preview`, `POST /tenants/{tenant_id}/business-detections/preview`, `POST /tenants/{tenant_id}/business-escalations/preview`, `POST /tenants/{tenant_id}/business-action-plans/preview`, `POST /tenants/{tenant_id}/business-notifications/preview`, `POST /tenants/{tenant_id}/business-briefings/preview` | `bash scripts/check_public_business_control_tower.sh && bash scripts/check_public_demo_api.sh` |
| Business intake pipeline | Preview-only provider event pipeline turns CRM/bank/accounting signals into safe payloads, role workbench cards, detection, approval-gated action plan, and draft-only notifications without persistence or external calls. | `docs/public/BUSINESS_INTAKE_PIPELINE.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-intake-pipeline`, `POST /tenants/{tenant_id}/business-intake-pipeline/preview`, `businessIntakePipeline` | `bash scripts/check_public_business_intake_pipeline.sh && bash scripts/check_public_demo_api.sh` |
| Business task handoff | Preview-only operator handoff turns approved action steps into internal task cards, internal outbox candidates, and draft in-app notifications without persistence, external provider writes, or external delivery. | `docs/public/BUSINESS_TASK_HANDOFF.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-task-handoff`, `POST /tenants/{tenant_id}/business-task-handoffs/preview`, `businessTaskHandoff` | `bash scripts/check_public_business_task_handoff.sh && bash scripts/check_public_demo_api.sh` |
| Business notification channels | Preview-only channel matrix shows in-app readiness plus Telegram, email, SMS, and webhook draft-only states with private secret gates and no external delivery. | `docs/public/BUSINESS_NOTIFICATION_CHANNELS.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-notification-channels`, `POST /tenants/{tenant_id}/business-notification-channels/preview`, `businessNotificationChannels` | `bash scripts/check_public_business_notification_channels.sh && bash scripts/check_public_demo_api.sh` |
| Business Context Assistant | Preview-only Business Context Assistant turns CRM, bank, accounting, and legal-reference facts into safe context cards, insight rules, and next actions without external provider writes. | `docs/public/BUSINESS_CONTEXT_ASSISTANT.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-context-assistant`, `POST /tenants/{tenant_id}/business-workbench-context/preview`, `businessContextAssistant` | `bash scripts/check_public_business_context_assistant.sh && bash scripts/check_public_demo_api.sh` |
| Business action execution | Preview-only action execution turns suggested actions into idempotent dry-run candidates, preflight checks, approval gates, rollback notes, and safe no-provider-write boundaries. | `docs/public/BUSINESS_ACTION_EXECUTION.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-action-execution`, `POST /tenants/{tenant_id}/business-action-executions/preview`, `businessActionExecution` | `bash scripts/check_public_business_action_execution.sh && bash scripts/check_public_demo_api.sh` |
| Business approval gateway | Preview-only approval gateway turns provider-changing execution candidates into approval requests, policy checks, approver routing, blocked commit unlocks, and audit trail evidence. | `docs/public/BUSINESS_APPROVAL_GATEWAY.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-approval-gateway`, `POST /tenants/{tenant_id}/business-approval-gateway/preview`, `businessApprovalGateway` | `bash scripts/check_public_business_approval_gateway.sh && bash scripts/check_public_demo_api.sh` |
| Integration runtime | Integration Runtime turns adapter operation contracts into a public-safe execution path: scope and idempotency preflight, approval dependency, outbox handoff, worker boundary, reconciliation plan, and incident routes without provider calls. | `docs/public/INTEGRATION_RUNTIME.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/integration-runtime`, `POST /tenants/{tenant_id}/integration-runtime/preview`, `integrationRuntime`, `adapter_runtime.previewed` | `bash scripts/check_public_integration_runtime.sh && bash scripts/check_public_demo_api.sh` |
| Integration execution | Integration Execution turns runtime intent into a public-safe run ledger and timeline: accepted request, preflight, approval gate, outbox enqueue, worker dispatch, blocked provider call, retry, reconciliation, incident route, and operator closure. | `docs/public/INTEGRATION_EXECUTION.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/integration-execution`, `POST /tenants/{tenant_id}/integration-executions/preview`, `integrationExecution`, `integration_execution.run_ledger_prepared` | `bash scripts/check_public_integration_execution.sh && bash scripts/check_public_demo_api.sh` |
| Business scenario replay | Reusable Business OS scenarios show external signal ingestion, safe normalization, cross-system detection, workbench context, recommended actions, and approval-aware automation across CRM/bank/accounting, support/SLA, and procurement/payment paths. | `docs/public/BUSINESS_SCENARIO_REPLAY.md`, `apps/admin/public-demo/index.html`, `GET /demo/public`, `GET /demo/business-scenario-replay`, `businessScenarioReplay` | `bash scripts/check_public_business_scenario_replay.sh && bash scripts/check_public_demo_api.sh` |
| Integration hub | Adapter catalog, provider connector guide, connector certification path, connector fixture replay, standalone replay API, Integration Runtime, Integration Execution, Adapter Studio, adapter developer guide, CRM deal intake, adapter auth profiles, secret-boundary metadata, mapping, scopes, operation scenarios, typed SDK operation plans, operation contracts, diagnostics, reconciliation, incident cards, and operator review are represented with public-safe providers. | `apps/admin/public-demo/index.html`, `GET /demo/connector-fixture-replay`, `GET /demo/integration-runtime`, `GET /demo/integration-execution`, `docs/public/PROVIDER_CONNECTOR_GUIDE.md`, `docs/public/CONNECTOR_CERTIFICATION.md`, `docs/public/CONNECTOR_FIXTURE_REPLAY.md`, `docs/public/INTEGRATION_RUNTIME.md`, `docs/public/INTEGRATION_EXECUTION.md`, `docs/public/ADAPTER_DEVELOPER_GUIDE.md`, `docs/public/INTEGRATION_ADAPTER_CATALOG.md`, `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`, `docs/public/INTEGRATION_RECONCILIATION.md`, `docs/public/CLIENT_SDK.md`, `docs/public/evidence/connector-certification.sanitized.json`, `docs/public/evidence/connector-fixture-replay.sanitized.json`, `examples/connector-fixtures/replay-fixtures.sanitized.json`, `docs/adr/0072-mock-crm-deal-adapter.md`, `docs/adr/0073-adapter-auth-profile-boundary.md`, `docs/adr/0074-public-safe-connector-certification.md`, `docs/adr/0075-public-safe-connector-fixture-replay.md` | `bash scripts/check_public_provider_connector_guide.sh && bash scripts/check_public_connector_certification.sh && bash scripts/check_public_connector_fixture_replay.sh && bash scripts/check_public_integration_runtime.sh && bash scripts/check_public_integration_execution.sh && bash scripts/check_public_adapter_developer_guide.sh && bash scripts/check_public_demo_api.sh && bash scripts/check_public_demo_sdk.sh` |
| Recovery and release safety | Backup/restore, rollback, SLO canary gate, and staged promotion drills use sanitized synthetic evidence. | `docs/public/BACKUP_RESTORE_EVIDENCE.md`, `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` | `bash scripts/check_public_backup_restore.sh && bash scripts/check_public_release_rollback.sh && bash scripts/check_public_slo_canary_gate.sh && bash scripts/check_public_staged_promotion.sh` |
| GitOps and IaC | Helm, Argo CD, OpenTofu, image automation, drift detection, and remediation are modeled with public-safe manifests and evidence. | `docs/public/GITOPS_DELIVERY.md`, `docs/public/GITOPS_IMAGE_AUTOMATION.md`, `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` | `bash scripts/check_public_helm_render.sh && bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh && bash scripts/check_public_infra_state_drift.sh` |
| Evidence boundary | Public export contains synthetic data and sanitized evidence only. | `PUBLIC_EXPORT_MANIFEST.md`, `docs/public/SANITIZED_EVIDENCE.md`, `docs/public/evidence/*.sanitized.json` | `bash scripts/check_public_export_secrets.sh` |
| Capability map | Each visible capability is linked to implementation surface, evidence, and verifier command. | `docs/public/TECHNICAL_CAPABILITY_MAP.md` | `bash scripts/check_public_technical_capability_map.sh` |
| Evidence index | Public capability groups are indexed as machine-readable docs, evidence files, verifier commands, public URLs, and boundary notes. | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json` | `bash scripts/check_public_evidence_index.sh` |
| Observability proof | Metrics, structured logs, alerts, runbooks, and dashboard panels are represented with public-safe synthetic evidence. | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/evidence/observability-proof.sanitized.json` | `bash scripts/check_public_observability_proof.sh` |
| Alert routing | Alertmanager-style routes, receivers, dedupe keys, escalation, silences, and runbook bindings are represented in evidence and the demo Operations tab. | `apps/admin/public-demo/index.html`, `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/evidence/alert-routing.sanitized.json` | `bash scripts/check_public_alert_routing.sh && bash scripts/check_public_demo_api.sh` |
| Incident response | Runbook-backed incidents, owners, mitigation, recovery timeline, and resolution evidence are represented in the demo Incidents tab. | `apps/admin/public-demo/index.html`, `docs/public/INCIDENT_RESPONSE_DEMO.md`, `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md` | `bash scripts/check_public_demo_api.sh && bash scripts/check_public_engineering_proof.sh` |

## Current Limits

- The public repository is a sanitized engineering surface, not the private
  product source.
- Public evidence uses synthetic data and public-safe manifests.
- The hosted demo is static-first through GitHub Pages; the API contract can be
  run locally with `bash scripts/run_public_demo_local.sh`.
- Real customer data, private infrastructure addresses, credentials, raw logs,
  payment provider details, and production deployment state are not included.
- Mobile apps, commercial onboarding, and authenticated real external-provider adapters are
  outside the current public surface.

## Next Engineering Work

Longer public-safe direction lives in `docs/public/ROADMAP.md`.

1. Add more real-provider notification adapter evidence on top of the
   public-safe channel matrix without exposing private secrets.
2. Expand the public observability proof into richer synthetic dashboard
   examples.
3. Deepen the admin frontend shell around the existing API and public demo
   contract.
4. Keep public and private repositories separated through the export gate and
   secret boundary checks.

## Verification

```bash
bash scripts/ci_smoke_public.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_evidence_index.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_connector_certification.sh
bash scripts/check_public_connector_fixture_replay.sh
bash scripts/check_public_adapter_developer_guide.sh
bash scripts/check_public_business_control_tower.sh
bash scripts/check_public_business_intake_pipeline.sh
bash scripts/check_public_business_task_handoff.sh
bash scripts/check_public_business_notification_channels.sh
bash scripts/check_public_business_context_assistant.sh
bash scripts/check_public_business_action_execution.sh
bash scripts/check_public_business_approval_gateway.sh
bash scripts/check_public_integration_runtime.sh
bash scripts/check_public_integration_execution.sh
bash scripts/check_public_business_scenario_replay.sh
bash scripts/check_public_export_secrets.sh
```
