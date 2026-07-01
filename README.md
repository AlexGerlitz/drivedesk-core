# DriveDesk Core

[![CI](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/ci.yml)

DriveDesk Core is the public backend/platform foundation behind the DriveDesk AI
Operator direction: business operations, integrations, workflows, audit/outbox,
adapter boundaries, recovery paths, and public proof owned by backend code.

This repository is meant to be reviewed as an engineering proof surface, not as
a narrow demo. The API, data model, public demo, CI gates, OpenAPI, SDK drift
checks, operations docs, and sanitized evidence all point to the same system
shape.

Profile / contact route: [DriveDesk AI Operator proof route](https://alexgerlitz.github.io/AlexGerlitz/drivedesk-proof-route.html),
[Decision-Ready Contact](https://alexgerlitz.github.io/AlexGerlitz/decision-ready-contact.html),
[LinkedIn message route](https://www.linkedin.com/in/alex-gerlitz-a659ab3bb/),
[PDF resume](https://alexgerlitz.github.io/AlexGerlitz/output/pdf/alex-gerlitz-python-backend-automation-resume.pdf),
[portfolio](https://alexgerlitz.github.io/AlexGerlitz/),
[enterprise readiness](https://alexgerlitz.github.io/AlexGerlitz/enterprise-readiness.html), and
[inbound brief](https://alexgerlitz.github.io/AlexGerlitz/intake-brief.html).

Message me first when there is one messy business workflow, one risky integration
boundary, or one backend/platform/DevOps slice that should become testable, logged,
documented, and handed off.

Shortest proof path: [LinkedIn Recruiter Packet](https://alexgerlitz.github.io/AlexGerlitz/linkedin-recruiter-packet.html) ->
[Hiring Decision](https://alexgerlitz.github.io/AlexGerlitz/hiring-decision.html) ->
[DriveDesk Proof Route](https://alexgerlitz.github.io/AlexGerlitz/drivedesk-proof-route.html) ->
[Decision-Ready Contact](https://alexgerlitz.github.io/AlexGerlitz/decision-ready-contact.html) ->
[PDF resume](https://alexgerlitz.github.io/AlexGerlitz/output/pdf/alex-gerlitz-remote-ai-automation-resume.pdf).

First useful result: a verified operations/integration platform slice with backend-owned
state, tests, logs, docs, and a handoff route.

## 60-Second Review

Hiring relevance: I can turn business operations, CRM/ERP adapters, audit/outbox
state, tenant boundaries, RBAC, workflow rules, integration recovery, metrics,
Docker, CI, OpenAPI, and public-safe evidence into a backend/platform system a
team can review, run, extend, and hand off.

| Signal | What to inspect |
| --- | --- |
| Backend/platform foundation | FastAPI, PostgreSQL/Alembic, tenant model, RBAC, audit log, outbox, workflow rules, workers, and metrics. |
| Integration discipline | Adapter catalog, connector certification, provider onboarding, fixture replay, idempotent handoff boundaries, and repair workbench. |
| Production proof | Docker Compose, OpenAPI/SDK drift checks, CI, public demo health, backup/restore, rollback, SLO canary, GitOps, and OpenTofu evidence. |
| Fast proof route | `docs/public/PUBLIC_REVIEW_BUNDLE.md`, `docs/public/SYSTEM_REVIEW_PATH.md`, `docs/public/STACK_REVIEW_BRIEF.md`, and `docs/public/PUBLIC_VERIFICATION_MATRIX.md`. |

Best-fit signal:

- operations platform backend, not a prompt-only or no-code-only workflow;
- backend-owned state, audit, retries, quality gates, and integration contracts;
- Business OS route from business event -> workflow -> adapter -> incident -> proof;
- public-safe evidence that lets a reviewer verify claims from code, docs, demo,
  checks, and GitHub Actions.

[![Public Demo Health](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/public-demo-health.yml/badge.svg)](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/public-demo-health.yml)

## Live Demo

[Open the public DriveDesk Core engineering reference](https://alexgerlitz.github.io/drivedesk-core/)

[Open the public DriveDesk Core demo](https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/)

![DriveDesk Core demo overview](docs/public/assets/drivedesk-core-demo-overview.png)

## Implemented Surface

- API/runtime: FastAPI API, PostgreSQL migrations with Alembic, background
  worker, Docker Compose local runtime, `GET /metrics`, pytest coverage, and
  architecture docs/ADRs.
- SaaS core: tenants, users, memberships, RBAC, bearer-token auth, current-user
  lookup, token revocation, redacted session listing, tenant isolation, and
  platform-admin grants.
- Business operations: tenant-owned contracts, payments, lessons, tasks,
  documents, lifecycle transitions, workflow rules, workflow actions, task
  creation, adapter-sync requests, and aggregate metrics.
- Integration layer: synthetic file import adapter, retry/dead-letter state,
  runtime adapter catalog, connector certification, provider onboarding,
  Integration Repair, action preview, fixture replay, and sandbox dry-run
  evidence.
- Public proof: Business OS tour, Review Console, generated OpenAPI client SDK
  example, OpenAPI drift check, public-safe backup/restore drill, release
  rollback drill, DevOps/platform milestone evidence, and public demo payloads.

## Start Here

| Need | Open | What it proves |
| --- | --- | --- |
| One-command review | `docs/public/PUBLIC_REVIEW_BUNDLE.md` | The shortest checked route through the public entrypoint, docs, demo health, OpenAPI, SDK, evidence, observability, alert routing, and proof contract. |
| Review Console | `docs/public/REVIEW_CONSOLE.md` | Browser-visible readiness, gates, evidence, handoff, remaining work, and public/private boundary. |
| Fast system route | `docs/public/SYSTEM_REVIEW_PATH.md` | How the public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index fit together. |
| Business OS tour | `docs/public/PLATFORM_TOUR.md` | How business events, Control Tower, Adapter Studio, incidents, and proof connect. |
| Stack brief | `docs/public/STACK_REVIEW_BRIEF.md` | What each major technology does, what is validated, what remains, and how to explain the stack. |
| Verification matrix | `docs/public/PUBLIC_VERIFICATION_MATRIX.md` | Which artifact and command proves each engineering claim. |
| Live product surface | [public engineering reference](https://alexgerlitz.github.io/drivedesk-core/) and [public demo](https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/) | Browser-visible workflow, operations, incidents, and proof tabs on synthetic demo data. |
| Current project state | `docs/public/PROJECT_STATUS.md` | What is implemented, what is intentionally public-safe, and what remains private. |
| Verification commands | `bash scripts/ci_smoke_public.sh` | Public smoke path covering docs, demo contract, OpenAPI, SDK examples, and release evidence. |

## System Snapshot

| Layer | Public evidence |
| --- | --- |
| Runtime | FastAPI demo API, background-worker contract, Postgres-shaped repositories, Redis/outbox job model, and `GET /metrics`. |
| Product core | Tenants, RBAC, audit log, outbox recovery, business records, lifecycle policies, workflow rules, tasks, and documents. |
| Integration hub | Adapter catalog, connector certification workbench, provider onboarding workbench, integration repair workbench, connector fixture replay, Adapter Studio, connection scopes, mapping validation, mapping transform preview, operation contracts, diagnostics, reconciliation, and operator review. |
| Operations | Prometheus-style metrics, structured logs, Alertmanager-style routing, incident response, backup/restore, rollback, SLO canary, and staged promotion evidence. |
| Delivery | Docker Compose, Helm chart, GitOps manifests, OpenTofu plan evidence, CI gates, Pages health check, and public/private export gate. |

## Fast Review

Start with `docs/public/PUBLIC_REVIEW_BUNDLE.md`, then run:

```bash
bash scripts/run_public_review_bundle.sh
```

This gives the shortest executable route through the public engineering surface.

Then open `docs/public/SYSTEM_REVIEW_PATH.md`, followed by
`docs/public/PLATFORM_TOUR.md`.

It gives the compact route through the public root, demo, API, SDK, operations
evidence, release safety, GitOps, OpenTofu, and evidence index.

The Platform Tour gives the Business OS route through business event ->
workflow -> adapter -> incident -> proof.

Then continue with `docs/public/REVIEWER_QUICKSTART.md`.

It gives a 5-minute pass, 15-minute verification path, and 45-minute deep
check for the public verification surface.

Use `docs/public/STACK_REVIEW_BRIEF.md` when you need the stack map in
plain engineering language: backend, data, workers, OpenAPI, adapters, Docker,
Kubernetes, GitOps, OpenTofu, CI/CD, observability, reliability, and
public/private boundaries. Validate it with
`bash scripts/check_public_stack_review_brief.sh`.

Use `docs/public/ENGINEERING_REVIEW_GUIDE.md` when you need the expanded
verification path.

It maps the live demo, public CI, proof contract, OpenAPI, generated SDK,
recovery drills, release gates, GitOps, OpenTofu, and public/private boundary
into one short verification path.

Use `docs/public/PUBLIC_VERIFICATION_MATRIX.md` when you need a compact
claim-to-evidence checklist with pass signals and verifier commands.

Use `docs/public/PROJECT_STATUS.md` when you need the current engineering
state, public-safe limits, and next work in one page.

Use `docs/public/TECHNICAL_CAPABILITY_MAP.md` when you need a direct
capability-to-evidence matrix with verifier commands.

Use `docs/public/EVIDENCE_INDEX.md` when you need the machine-readable
capability-to-evidence index, verifier list, public URLs, and boundary notes.

Use `docs/public/PUBLIC_REVIEW_BUNDLE.md` when you need the fastest
one-command public review route.

Use `docs/public/REVIEW_CONSOLE.md` when you need the browser-visible readiness
console for current gates, evidence, handoff, remaining work, and public/private
boundary. Its machine-readable evidence is
`docs/public/evidence/review-console.sanitized.json`.

Use `docs/public/CONNECTOR_CERTIFICATION.md` when you need the provider-neutral
path for turning CRM, bank, accounting, ERP, KKT, webhook, file, email,
telephony, or custom API systems into DriveDesk connectors.

Use `docs/public/PROVIDER_ONBOARDING.md` when you need the concrete onboarding
workbench for moving one provider from catalog profile to mapping preview,
preflight checks, sandbox dry-run, approval review, private rollout, and
monitored reconciliation.

Use `docs/public/INTEGRATION_REPAIR.md` when you need the operator repair path
for retry, dead-letter, reconciliation mismatch, impact analysis, safe actions,
approval gates, and postcheck evidence.

Use `docs/public/CONNECTOR_FIXTURE_REPLAY.md` when you need the replayable
synthetic fixture proof for happy path, redaction, invalid payload, retry,
dead-letter, and reconciliation connector behavior.

Use `docs/public/OBSERVABILITY_PROOF.md` when you need the public-safe
metrics, structured logs, alert, runbook, and dashboard evidence path.

Use `docs/public/NOTIFICATION_DELIVERY.md` when you need the public-safe
notification delivery path from safe draft to outbox, worker, provider gate,
retry, dead-letter, operator review, and observability.

Use `docs/public/ALERT_ROUTING_EVIDENCE.md` when you need the public-safe
alert route, receiver, dedupe, escalation, silence, and runbook binding path.

Use `docs/public/INCIDENT_RESPONSE_DEMO.md` when you need the public-safe
incident queue, mitigation, recovery, and resolution evidence path.

## Verification Path

1. Start with `docs/public/PUBLIC_REVIEW_BUNDLE.md`.
2. Run `bash scripts/run_public_review_bundle.sh`.
3. Open `docs/public/SYSTEM_REVIEW_PATH.md`.
4. Open `docs/public/PLATFORM_TOUR.md`.
5. Continue with `docs/public/REVIEWER_QUICKSTART.md`.
6. Review `docs/public/STACK_REVIEW_BRIEF.md`.
7. Open the live demo and switch to the Workflow, Control Tower, Integrations, Operations, Incidents, and Proof tabs.
8. Inspect `docs/openapi.json`.
9. Run `bash scripts/check_public_system_review_path.sh`.
10. Run `bash scripts/check_public_platform_tour.sh`.
11. Run `bash scripts/check_public_stack_review_brief.sh`.
12. Run `bash scripts/ci_smoke_public.sh`.
13. Run `bash scripts/check_public_engineering_proof.sh`.
14. Run `bash scripts/check_public_demo_api.sh`.
15. Run one generated client example from `examples/`.
16. Run `bash scripts/check_public_verification_matrix.sh`.
17. Review `docs/public/PROJECT_STATUS.md`, `docs/public/TECHNICAL_CAPABILITY_MAP.md`, `docs/public/PUBLIC_VERIFICATION_MATRIX.md`, `docs/public/EVIDENCE_INDEX.md`, `docs/public/STACK_REVIEW_BRIEF.md`, `docs/public/PUBLIC_REVIEW_BUNDLE.md`, `docs/public/PUBLIC_DEMO_HEALTH.md`, `docs/public/OPENAPI_DRIFT.md`, `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/OBSERVABILITY_DASHBOARD.md`, `docs/public/NOTIFICATION_DELIVERY.md`, `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/INCIDENT_RESPONSE_DEMO.md`, `docs/public/ENGINEERING_PROOF.md`, `docs/public/PLATFORM_MATURITY_70.md`, and `docs/public/SANITIZED_EVIDENCE.md`.
18. Review `docs/public/SYSTEM_DESIGN.md`, `docs/public/PROVIDER_CONNECTOR_GUIDE.md`, `docs/public/CONNECTOR_CERTIFICATION.md`, `docs/public/PROVIDER_ONBOARDING.md`, `docs/public/INTEGRATION_REPAIR.md`, `docs/public/CONNECTOR_FIXTURE_REPLAY.md`, `docs/public/ADAPTER_DEVELOPER_GUIDE.md`, `docs/public/GITOPS_DELIVERY.md`, and the recovery evidence docs.

## Full Artifact Reference

- `docs/public/ENGINEERING_CASE_STUDY.md` - engineering case study.
- `docs/public/SYSTEM_REVIEW_PATH.md` - compact engineering route through the public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index.
- `docs/public/PLATFORM_TOUR.md` - Business OS tour across business events, Control Tower, Adapter Studio, incidents, proof, and verification gates.
- `docs/public/REVIEWER_QUICKSTART.md` - shortest external verification path with 5-minute, 15-minute, and 45-minute verification tracks.
- `docs/public/STACK_REVIEW_BRIEF.md` - stack map explaining what each
  technology does, what is validated, and what remains.
- `docs/public/PUBLIC_REVIEW_BUNDLE.md` - one-command public review route with a machine-readable evidence contract.
- `docs/public/evidence/stack-review-brief.sanitized.json` - machine-readable
  stack brief evidence.
- `docs/public/evidence/public-review-bundle.sanitized.json` - machine-readable public review bundle evidence.
- `docs/public/ENGINEERING_REVIEW_GUIDE.md` - short verification path for demo, CI, API, recovery, GitOps, and IaC evidence.
- `docs/public/PUBLIC_VERIFICATION_MATRIX.md` - claim-to-evidence matrix with verifier commands and pass signals.
- `docs/public/PROJECT_STATUS.md` - current public-safe engineering status, limits, and next work.
- `docs/public/TECHNICAL_CAPABILITY_MAP.md` - capability-to-evidence map with verifier commands.
- `docs/public/EVIDENCE_INDEX.md` - machine-readable capability-to-evidence index contract.
- `docs/public/PUBLIC_DEMO_HEALTH.md` - public-safe Pages/demo health
  workflow, static fallback, OpenAPI, SDK, and evidence contract.
- `docs/public/evidence/public-demo-health.sanitized.json` - machine-readable
  public demo health evidence.
- `docs/public/OPENAPI_DRIFT.md` - public-safe OpenAPI drift contract.
- `docs/public/evidence/openapi-drift.sanitized.json` - machine-readable
  OpenAPI drift evidence.
- `docs/public/OBSERVABILITY_PROOF.md` - public-safe metrics, logs, alerts, and dashboard evidence.
- `docs/public/OBSERVABILITY_DASHBOARD.md` - public-safe Grafana-style dashboard groups, panel queries, alert links, runbooks, and redaction boundaries.
- `docs/public/NOTIFICATION_DELIVERY.md` - public-safe notification delivery runtime for adapter profiles, outbox, worker, retry, dead-letter, and observability.
- `docs/public/ALERT_ROUTING_EVIDENCE.md` - public-safe alert routing, dedupe, escalation, and silence evidence.
- `docs/public/INCIDENT_RESPONSE_DEMO.md` - public-safe incident queue,
  mitigation, recovery, and resolution evidence.
- `docs/public/ENGINEERING_PROOF.md` - proof tab payload, gates, evidence, and verifier contract.
- `docs/public/SYSTEM_DESIGN.md` - system design overview.
- `docs/public/API_BACKED_DEMO.md` - read-only synthetic demo API contract.
- `docs/public/WORKFLOW_DEMO.md` - synthetic business workflow contract.
- `docs/public/WORKFLOW_RULES.md` - tenant-owned workflow rules contract.
- `docs/public/WORKFLOW_ACTION_RUNS.md` - workflow action execution history.
- `docs/public/AUTH_FOUNDATION.md` - auth, bearer token, and RBAC overview.
- `docs/public/AUTH_OBSERVABILITY.md` - auth metrics, alert names, and runbook shape.
- `docs/public/SESSION_REVOCATION.md` - admin-triggered tenant/platform session revocation.
- `docs/public/PLATFORM_ADMIN.md` - dedicated platform-admin model and SaaS control-plane boundary.
- `docs/public/TENANT_ISOLATION.md` - tenant isolation and bootstrap boundary overview.
- `docs/public/BUSINESS_RECORDS.md` - tenant-owned business record foundation.
- `docs/public/BUSINESS_RECORD_LIFECYCLE.md` - lifecycle policy catalog and preview validation.
- `docs/public/CLIENT_SDK.md` - generated OpenAPI client SDK example.
- `docs/public/PROVIDER_CONNECTOR_GUIDE.md` - public-safe connector path for future authenticated providers.
- `docs/public/CONNECTOR_CERTIFICATION.md` - public-safe certification path for provider profile, capability manifest, contract fixtures, runtime readiness, and release proof.
- `docs/public/PROVIDER_ONBOARDING.md` - public-safe provider onboarding workbench for profile, mapping, preflight, sandbox dry-run, approval, rollout, and reconciliation.
- `docs/public/INTEGRATION_REPAIR.md` - public-safe integration repair workbench for runbook-backed retry, dead-letter, reconciliation mismatch, impact, safe actions, approval, and postcheck evidence.
- `docs/public/CONNECTOR_FIXTURE_REPLAY.md` - public-safe fixture replay path for happy path, redaction, invalid payload, retry, dead-letter, and reconciliation.
- `docs/public/ADAPTER_DEVELOPER_GUIDE.md` - public-safe adapter developer path from generated SDK operation plans to private connector implementation.
- `docs/public/INTEGRATION_ADAPTER_CATALOG.md` - runtime adapter metadata and discovery contract.
- `docs/public/INTEGRATION_MAPPING_VALIDATION.md` - mapping validation against adapter requirements.
- `docs/public/INTEGRATION_MAPPING_TRANSFORM.md` - runtime mapping transform and preview.
- `docs/public/INTEGRATION_CONNECTION_SCOPES.md` - least-privilege connection scopes.
- `docs/public/INTEGRATION_OPERATION_CONTRACTS.md` - operation-level adapter contracts.
- `docs/public/INTEGRATION_ACCOUNTING_EXPORT.md` - executable outbound accounting export adapter.
- `docs/public/INTEGRATION_CONNECTION_DIAGNOSTICS.md` - safe connection health-checks and metrics.
- `docs/public/INTEGRATION_RECONCILIATION.md` - safe provider evidence comparison and diff.
- `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md` - runbook-backed incident cards for integration signals.
- `docs/public/INTEGRATION_OPERATOR_REVIEW.md` - safe review queue for failed integration jobs.
- `docs/public/INTEGRATION_CONNECTIONS.md` - tenant-owned adapter profiles and mapping.
- `docs/public/INTEGRATION_ADAPTERS.md` - adapter contract and retry model.
- `docs/public/INTEGRATION_OBSERVABILITY.md` - adapter metrics and worker log signals.
- `docs/public/OUTBOX_RECOVERY.md` - audited operator retry path for failed outbox jobs.
- `docs/public/BACKUP_RESTORE_EVIDENCE.md` - public-safe synthetic backup and restore drill.
- `docs/public/RELEASE_ROLLBACK_EVIDENCE.md` - public-safe bad-release rollback drill.
- `docs/public/SLO_CANARY_GATE_EVIDENCE.md` - public-safe SLO canary promotion gate drill.
- `docs/public/STAGED_PROMOTION_EVIDENCE.md` - public-safe staged release promotion drill.
- `docs/public/HELM_CHART.md` - public-safe Helm chart foundation.
- `docs/public/GITOPS_DELIVERY.md` - public-safe GitOps delivery foundation.
- `docs/public/GITOPS_PROMOTION_DRIFT.md` - public-safe GitOps image promotion and drift evidence.
- `docs/public/GITOPS_DRIFT_REMEDIATION.md` - public-safe GitOps drift remediation evidence.
- `docs/public/GITOPS_IMAGE_AUTOMATION.md` - public-safe GitOps image automation evidence.
- `docs/public/OPENTOFU_PLAN_EVIDENCE.md` - public-safe OpenTofu plan evidence.
- `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` - public-safe infrastructure state drift evidence.
- `docs/public/RUNTIME_ROLLOUT_EVIDENCE.md` - public-safe private staging runtime rollout evidence.
- `docs/public/PRIVATE_INFRA_VALIDATION.md` - public-safe private infrastructure validation evidence.
- `docs/public/PRIVATE_INFRA_REMEDIATION.md` - public-safe private infrastructure remediation plan evidence.
- `docs/public/PRIVATE_INFRA_REMEDIATION_EXECUTION.md` - public-safe private infrastructure remediation execution evidence.
- `docs/public/PRIVATE_INFRA_POST_REMEDIATION_DRIFT_REFRESH.md` - public-safe post-remediation drift refresh evidence.
- `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md` - public-safe recurring scheduled validation evidence.
- `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md` - public-safe scheduled validation alerting evidence.
- `docs/public/PLATFORM_MATURITY_70.md` - public-safe 70 percent DevOps/platform milestone.
- `docs/public/OBSERVABILITY_PROOF.md` - public-safe observability proof.
- `docs/public/OBSERVABILITY_DASHBOARD.md` - public-safe observability dashboard contract.
- `docs/public/NOTIFICATION_DELIVERY.md` - public-safe notification delivery contract.
- `docs/public/ALERT_ROUTING_EVIDENCE.md` - public-safe alert routing proof.
- `docs/public/INCIDENT_RESPONSE_DEMO.md` - public-safe incident response proof.
- `docs/public/ARCHITECTURE_DIAGRAMS.md` - architecture diagrams.
- `docs/public/SANITIZED_EVIDENCE.md` - sanitized staging evidence.
- `docs/public/PUBLIC_DEMO_PLAN.md` - future public demo plan.
- `docs/public/ROADMAP.md` - public-safe engineering roadmap.
- `apps/admin/public-demo/index.html` - static synthetic product demo shell.
- `docs/openapi.json` - generated FastAPI OpenAPI schema.
- `GET /demo/public` - read-only synthetic demo payload in the exported API.
- `GET /demo/connector-certification` - standalone public-safe provider
  readiness contract for connector certification stages, gates, and boundaries.
- `GET /demo/connector-fixture-replay` - standalone public-safe replay contract
  for connector fixture groups, redaction outcomes, and boundaries.
- `GET /demo/business-intake-pipeline` - standalone public-safe intake pipeline
  contract for provider signal previews, boundaries, and action planning.
- `GET /demo/business-task-handoff` - standalone public-safe task handoff
  contract for internal task cards, internal outbox candidates, and draft
  notifications.
- `GET /demo/business-notification-channels` - standalone public-safe
  notification matrix for in-app, Telegram, email, SMS, and webhook readiness.
- `GET /demo/notification-delivery` - standalone public-safe notification
  delivery runtime contract for `notificationDelivery`.
- `GET /demo/business-context-assistant` - standalone public-safe Business
  Context Assistant contract for `businessContextAssistant`.
- `GET /integration-adapters` - runtime adapter catalog endpoint.
- `POST /tenants/{tenant_id}/integration-mapping-preview` - read-only mapping transform preview.
- `file_import:preview` and `file_import:execute` - public-safe connection scope examples.
- `GET /metrics` - public-safe aggregate metrics including auth health.
- `POST /auth/sessions/{session_id}/revoke` - admin-triggered visible session revocation.
- `POST /platform/admins` - platform-admin grant endpoint.
- `GET /platform/admins` - platform-admin grant review endpoint.
- `POST /tenants/{tenant_id}/business-records` - tenant-owned business record creation.
- `GET /tenants/{tenant_id}/business-records` - tenant-owned business record listing.
- `POST /tenants/{tenant_id}/business-records/{record_id}/transition` - auditable business status transition.
- `drivedesk_business_records` - aggregate business record metric by type and status.
- `internal.business_record` - adapter key used by business record outbox events.
- `POST /tenants/{tenant_id}/workflow-rules` - tenant-owned workflow rule creation.
- `GET /tenants/{tenant_id}/workflow-rules` - tenant-owned workflow rule listing.
- `workflow.rule.triggered` - audit event for matching workflow rules.
- `workflow.contract_approved` - public-safe example workflow outbox event.
- `create_task_record` - workflow action that creates tenant-owned task records.
- `request_adapter_sync` - workflow action that requests retryable adapter work.
- `workflow.task_record.created` - workflow outbox event for task creation.
- `workflow.contract_sync.requested` - public-safe example adapter sync request.
- `drivedesk_workflow_rules` - aggregate workflow rule metric by status, trigger, and action.
- `internal.workflow` - adapter key used by workflow rule outbox events.
- `DriveDeskMetricsStorageUnavailable`, `DriveDeskAuthFailureSpike`, and
  `DriveDeskAuthLockedAttempts` - public-safe auth alert contract.
- `workflow`, `timeline`, and `domainEvents` - synthetic business process data
  in the public demo payload.
- `sdk/generated/public-demo/` - generated client SDK artifacts.
- `sdk/generated/public-demo/python/drivedesk_public_demo_client.py` - generated Python SDK client.
- `sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs` - generated JavaScript SDK client.
- `sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts` - generated TypeScript definitions.
- `scripts/generate_public_demo_sdk.py` - SDK generator from OpenAPI.
- `scripts/check_public_demo_sdk.sh` - generated SDK drift and runtime smoke.
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
- `scripts/check_public_system_review_path.sh` - public-safe compact system review path validation.
- `scripts/check_public_reviewer_quickstart.sh` - public-safe verification quickstart validation.
- `scripts/check_public_review_guide.sh` - public-safe short verification path validation.
- `scripts/check_public_provider_connector_guide.sh` - public-safe provider connector guide validation.
- `scripts/check_public_connector_certification.sh` - public-safe connector certification path validation.
- `scripts/check_public_provider_onboarding.sh` - public-safe provider onboarding validation.
- `scripts/check_public_provider_sandbox_dry_run.sh` - public-safe provider sandbox dry-run validation.
- `scripts/run_provider_sandbox_dry_run.py` - sanitized plan-only/fake/http operator CLI for provider sandbox dry-run.
- `scripts/record_provider_sandbox_dry_run_evidence.sh` - private-runtime evidence recorder for provider sandbox dry-run.
- `scripts/check_provider_sandbox_dry_run_evidence.py` - sanitized evidence verifier for provider sandbox dry-run.
- `scripts/check_public_integration_repair.sh` - public-safe integration repair validation.
- `scripts/check_public_connector_fixture_replay.sh` - public-safe connector fixture replay validation.
- `scripts/check_public_adapter_developer_guide.sh` - public-safe adapter developer guide and SDK operation-plan validation.
- `scripts/check_public_observability_proof.sh` - public-safe observability proof validation.
- `scripts/check_public_observability_dashboard.sh` - public-safe observability dashboard validation.
- `scripts/check_public_notification_delivery.sh` - public-safe notification delivery validation.
- `scripts/check_public_alert_routing.sh` - public-safe alert routing validation.
- `scripts/check_public_engineering_proof.sh` - public-safe proof tab and evidence contract validation.
- `scripts/check_public_gitops_layout.sh` - public-safe GitOps layout validation.
- `scripts/check_public_gitops_image_automation.sh` - public-safe GitOps image automation validation.
- `scripts/check_public_gitops_promotion_drift.sh` - public-safe GitOps promotion and drift validation.
- `scripts/check_public_gitops_drift_remediation.sh` - public-safe GitOps drift remediation validation.
- `scripts/run_public_demo_local.sh` - one-command local API run.
- `scripts/check_public_demo_api.sh` - local API contract and examples smoke.
- `examples/curl/demo-public.sh` - curl client example.
- `examples/python/demo_public_client.py` - Python client example.
- `examples/python/demo_adapter_operation_plan.py` - Python adapter operation plan SDK example.
- `examples/js/demo-public-fetch.js` - JavaScript fetch client example.
- `examples/js/demo-adapter-operation-plan.mjs` - JavaScript adapter operation plan SDK example.

## Local Run

```bash
python -m pip install -r requirements.txt
bash scripts/run_public_demo_local.sh
```

Health:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/demo/public
curl http://localhost:8080/demo/connector-fixture-replay
curl http://localhost:8080/demo/business-intake-pipeline
curl http://localhost:8080/demo/business-task-handoff
curl http://localhost:8080/demo/business-notification-channels
curl http://localhost:8080/demo/business-context-assistant
curl http://localhost:8080/demo/business-action-execution
curl http://localhost:8080/demo/business-approval-gateway
curl http://localhost:8080/demo/integration-runtime
curl http://localhost:8080/demo/integration-execution
curl http://localhost:8080/demo/integration-repair
# Authenticated tenant endpoint:
# POST /tenants/{tenant_id}/integration-repairs/preview
curl http://localhost:8080/demo/business-scenario-replay
```

API contract and client examples:

```bash
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/check_public_business_task_handoff.sh
bash scripts/check_public_business_notification_channels.sh
bash scripts/check_public_business_context_assistant.sh
bash scripts/check_public_business_action_execution.sh
bash scripts/check_public_business_approval_gateway.sh
bash scripts/check_public_integration_runtime.sh
bash scripts/check_public_integration_execution.sh
bash scripts/check_public_integration_repair.sh
bash scripts/check_public_backup_restore.sh
bash scripts/check_public_release_rollback.sh
bash scripts/check_public_slo_canary_gate.sh
bash scripts/check_public_staged_promotion.sh
bash scripts/check_public_helm_render.sh
bash scripts/check_public_opentofu_plan.sh
bash scripts/check_public_infra_state_drift.sh
bash scripts/check_public_runtime_rollout.sh
bash scripts/check_public_private_infra_validation.sh
bash scripts/check_public_private_infra_remediation.sh
bash scripts/check_public_private_infra_remediation_execution.sh
bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh
bash scripts/check_public_private_infra_scheduled_validation.sh
bash scripts/check_public_private_infra_scheduled_alerting.sh
bash scripts/check_public_platform_maturity_70.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_review_bundle.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_stack_review_brief.sh
bash scripts/check_public_verification_matrix.sh
bash scripts/check_public_review_guide.sh
bash scripts/check_public_pages_entrypoint.sh
bash scripts/check_public_demo_health.sh
bash scripts/check_public_openapi_drift.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_connector_certification.sh
bash scripts/check_public_provider_onboarding.sh
bash scripts/check_public_provider_sandbox_dry_run.sh
bash scripts/check_public_integration_repair.sh
bash scripts/check_public_connector_fixture_replay.sh
bash scripts/check_public_adapter_developer_guide.sh
bash scripts/check_public_evidence_index.sh
bash scripts/check_public_review_console.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_observability_dashboard.sh
bash scripts/check_public_notification_delivery.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_gitops_layout.sh
bash scripts/check_public_gitops_image_automation.sh
bash scripts/check_public_gitops_promotion_drift.sh
bash scripts/check_public_gitops_drift_remediation.sh
BASE_URL=http://localhost:8080 bash examples/curl/demo-public.sh
BASE_URL=http://localhost:8080 python examples/python/demo_public_client.py
BASE_URL=http://localhost:8080 node examples/js/demo-public-fetch.js
BASE_URL=http://localhost:8080 python examples/python/demo_adapter_operation_plan.py
BASE_URL=http://localhost:8080 node examples/js/demo-adapter-operation-plan.mjs
```

Docker Compose:

```bash
docker compose -f infra/docker/docker-compose.foundation.yml up --build
```

## Checks

```bash
bash scripts/ci_smoke_public.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_backup_restore.sh
bash scripts/check_public_release_rollback.sh
bash scripts/check_public_slo_canary_gate.sh
bash scripts/check_public_staged_promotion.sh
bash scripts/check_public_helm_render.sh
bash scripts/check_public_opentofu_plan.sh
bash scripts/check_public_infra_state_drift.sh
bash scripts/check_public_runtime_rollout.sh
bash scripts/check_public_private_infra_validation.sh
bash scripts/check_public_private_infra_remediation.sh
bash scripts/check_public_private_infra_remediation_execution.sh
bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh
bash scripts/check_public_private_infra_scheduled_validation.sh
bash scripts/check_public_private_infra_scheduled_alerting.sh
bash scripts/check_public_platform_maturity_70.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_review_bundle.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_stack_review_brief.sh
bash scripts/check_public_verification_matrix.sh
bash scripts/check_public_review_guide.sh
bash scripts/check_public_pages_entrypoint.sh
bash scripts/check_public_demo_health.sh
bash scripts/check_public_openapi_drift.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_provider_connector_guide.sh
bash scripts/check_public_connector_certification.sh
bash scripts/check_public_provider_onboarding.sh
bash scripts/check_public_provider_sandbox_dry_run.sh
bash scripts/check_public_connector_fixture_replay.sh
bash scripts/check_public_adapter_developer_guide.sh
bash scripts/check_public_evidence_index.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_observability_dashboard.sh
bash scripts/check_public_notification_delivery.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_gitops_layout.sh
bash scripts/check_public_gitops_image_automation.sh
bash scripts/check_public_gitops_promotion_drift.sh
bash scripts/check_public_gitops_drift_remediation.sh
```

## Public Demo Shell

Open the hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

Or open this file directly in a browser:

```text
apps/admin/public-demo/index.html
```

For local API-backed mode, run the FastAPI app and open:

```text
apps/admin/public-demo/index.html?demoApi=http://localhost:8080/demo/public
```

## Architecture

- `docs/PROJECT_DIRECTION.md`
- `docs/DRIVEDESK_CORE.md`
- `docs/INFRASTRUCTURE_TARGET.md`
- `docs/DEVOPS_ROADMAP.md`
- `docs/public/README.md`
- `docs/public/ENGINEERING_CASE_STUDY.md`
- `docs/public/SYSTEM_DESIGN.md`
- `docs/public/API_BACKED_DEMO.md`
- `docs/public/WORKFLOW_DEMO.md`
- `docs/public/WORKFLOW_RULES.md`
- `docs/public/WORKFLOW_ACTION_RUNS.md`
- `docs/public/AUTH_FOUNDATION.md`
- `docs/public/AUTH_OBSERVABILITY.md`
- `docs/public/SESSION_REVOCATION.md`
- `docs/public/PLATFORM_ADMIN.md`
- `docs/public/TENANT_ISOLATION.md`
- `docs/public/BUSINESS_RECORDS.md`
- `docs/public/BUSINESS_RECORD_LIFECYCLE.md`
- `docs/public/CLIENT_SDK.md`
- `docs/public/PROVIDER_CONNECTOR_GUIDE.md`
- `docs/public/INTEGRATION_ADAPTER_CATALOG.md`
- `docs/public/INTEGRATION_MAPPING_VALIDATION.md`
- `docs/public/INTEGRATION_MAPPING_TRANSFORM.md`
- `docs/public/INTEGRATION_CONNECTION_SCOPES.md`
- `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`
- `docs/public/INTEGRATION_ACCOUNTING_EXPORT.md`
- `docs/public/INTEGRATION_CONNECTION_DIAGNOSTICS.md`
- `docs/public/INTEGRATION_RECONCILIATION.md`
- `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md`
- `docs/public/INTEGRATION_OPERATOR_REVIEW.md`
- `docs/public/INTEGRATION_CONNECTIONS.md`
- `docs/public/INTEGRATION_ADAPTERS.md`
- `docs/public/INTEGRATION_OBSERVABILITY.md`
- `docs/public/OUTBOX_RECOVERY.md`
- `docs/public/BACKUP_RESTORE_EVIDENCE.md`
- `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`
- `docs/public/SLO_CANARY_GATE_EVIDENCE.md`
- `docs/public/STAGED_PROMOTION_EVIDENCE.md`
- `docs/public/HELM_CHART.md`
- `docs/public/GITOPS_DELIVERY.md`
- `docs/public/GITOPS_PROMOTION_DRIFT.md`
- `docs/public/GITOPS_DRIFT_REMEDIATION.md`
- `docs/public/GITOPS_IMAGE_AUTOMATION.md`
- `docs/public/OPENTOFU_PLAN_EVIDENCE.md`
- `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md`
- `docs/public/ARCHITECTURE_DIAGRAMS.md`
- `docs/public/PUBLIC_DEMO_PLAN.md`
- `docs/public/SANITIZED_EVIDENCE.md`
- `docs/public/ROADMAP.md`
- `docs/openapi.json`
- `docs/adr/0001-modular-monolith-first.md`
- `docs/adr/0006-drivedesk-core-foundation.md`
- `docs/adr/0007-identity-rbac-audit-outbox-foundation.md`
- `docs/adr/0014-integration-adapter-foundation.md`
- `docs/adr/0015-core-auth-token-foundation.md`
- `docs/adr/0016-auth-lifecycle-audit-guard.md`
- `docs/adr/0017-bearer-tenant-isolation.md`
- `docs/adr/0018-tenant-scope-query-helpers.md`
- `docs/adr/0019-tenant-owned-repository-helpers.md`
- `docs/adr/0020-admin-visible-auth-session-listing.md`
- `docs/adr/0021-auth-observability-metrics.md`
- `docs/adr/0022-auth-security-alerts.md`
- `docs/adr/0023-dedicated-platform-admin-model.md`
- `docs/adr/0024-admin-triggered-session-revocation.md`
- `docs/adr/0025-tenant-owned-business-record-foundation.md`
- `docs/adr/0026-business-record-lifecycle-and-metrics.md`
- `docs/adr/0027-workflow-rule-foundation.md`
- `docs/adr/0028-workflow-actions-task-and-adapter-sync.md`
- `docs/adr/0029-workflow-action-run-observability.md`
- `docs/adr/0030-outbox-retry-recovery.md`
- `docs/adr/0031-tenant-owned-integration-connections.md`
- `docs/adr/0032-runtime-adapter-catalog.md`
- `docs/adr/0033-integration-mapping-validation.md`
- `docs/adr/0034-integration-mapping-transform-preview.md`
- `docs/adr/0035-integration-connection-scopes.md`
- `docs/adr/0036-structured-adapter-operation-contracts.md`
- `docs/adr/0037-integration-operator-review-queue.md`
- `docs/adr/0038-business-record-lifecycle-policy-catalog.md`
- `docs/adr/0039-mock-accounting-export-adapter.md`
- `docs/adr/0040-integration-connection-diagnostics.md`
- `docs/adr/0041-integration-reconciliation-evidence.md`
- `docs/adr/0042-integration-incident-runbooks.md`
- `docs/adr/0043-public-safe-backup-restore-drill.md`
- `docs/adr/0044-public-safe-release-rollback-drill.md`
- `docs/adr/0045-public-safe-slo-canary-gate-drill.md`
- `docs/adr/0046-public-safe-staged-promotion-drill.md`
- `docs/adr/0047-public-safe-helm-chart-foundation.md`
- `docs/adr/0048-public-safe-gitops-delivery-foundation.md`
