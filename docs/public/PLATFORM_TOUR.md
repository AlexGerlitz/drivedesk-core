# DriveDesk Platform Tour

This tour shows DriveDesk as a business operations platform, not only a demo
dashboard. It connects the public UI, API payload, generated SDK, integration
workbench, observability, recovery evidence, and release gates into one product
path.

Document path: `docs/public/PLATFORM_TOUR.md`.

The tour is public-safe: it uses synthetic data and sanitized evidence only.

## Product Path

| Step | Product surface | What happens | Evidence |
| --- | --- | --- | --- |
| 1 | Business signal | A synthetic lead, contract, payment, task, or external provider fact enters the platform. | `businessControlTower.providerIntake`, `workflowScenarios` |
| 2 | Workbench context | The operator gets role-specific context, risk level, source-system cards, suggested actions, the provider-event intake pipeline, task handoff preview, notification channel matrix, Business Context Assistant, action execution preview, and reusable scenario replay. | `businessControlTower.workbenchContext`, `businessIntakePipeline`, `businessTaskHandoff`, `businessNotificationChannels`, `businessContextAssistant`, `businessActionExecution`, `businessScenarioReplay`, `BUSINESS_INTAKE_PIPELINE.md`, `BUSINESS_TASK_HANDOFF.md`, `BUSINESS_NOTIFICATION_CHANNELS.md`, `BUSINESS_CONTEXT_ASSISTANT.md`, `BUSINESS_ACTION_EXECUTION.md`, `BUSINESS_SCENARIO_REPLAY.md`, `GET /demo/business-intake-pipeline`, `GET /demo/business-task-handoff`, `GET /demo/business-notification-channels`, `GET /demo/business-context-assistant`, `GET /demo/business-action-execution`, `GET /demo/business-scenario-replay`, `POST /tenants/{tenant_id}/business-workbench-context/preview`, `POST /tenants/{tenant_id}/business-action-executions/preview` |
| 3 | Workflow action | Business rules create audit events, internal task cards, notification channel drafts, execution dry-runs, outbox candidates, or adapter-sync requests. | `workflowScenarios`, `workflow.action_run.created`, `businessTaskHandoff`, `businessNotificationChannels`, `businessActionExecution` |
| 4 | Adapter Studio | Runtime catalog, connector certification, fixture replay, standalone replay API, and generated SDK operation plans show how an external provider is connected without exposing secrets. | `adapterStudio`, `connectorFixtureReplay`, `GET /demo/connector-fixture-replay`, `CONNECTOR_CERTIFICATION.md`, `CONNECTOR_FIXTURE_REPLAY.md`, `sdk/generated/public-demo/` |
| 5 | Async execution | Accepted work moves through outbox and worker-backed contracts with retry and idempotency boundaries. | `outbox`, `integrationJobs`, `worker:drivedesk_worker.main.process_pending_outbox` |
| 6 | Operations response | Metrics, alert routing, incidents, runbooks, and operator review make failures visible and recoverable. | `alertRouting`, `incidentResponse`, `drivedesk_integration_incidents` |
| 7 | Release proof | CI, public export, recovery drills, GitOps, OpenTofu, and Pages health prove the public surface stays consistent. | `engineeringProof`, `EVIDENCE_INDEX.md` |

## Demo Route

Use the public demo in this order:

1. `Overview` - system status, queue, timeline, and product-shaped metrics.
2. `Workflow` - automation scenarios and end-to-end chain.
3. `Control Tower` - provider intake, workbench context, detection, escalation,
   action plan, notification preview, role briefing, Business Intake Pipeline,
   Business Task Handoff, Notification Channels, Business Context Assistant,
   Business Action Execution,
   and Business Scenario Replay.
4. `Integrations` - Adapter Studio, connector certification, fixture replay,
   adapter contracts, operation scenarios, sync jobs, and health.
5. `Operations` - alert routing and recovery evidence.
6. `Incidents` - incident queue, timeline, recovery actions, and resolution
   evidence.
7. `Proof` - gates and evidence that bind UI, API, SDK, docs, and CI.

## Architecture Trace

```text
business event
  -> tenant-scoped core
  -> workflow rule
  -> audit/outbox/task
  -> adapter operation plan
  -> worker-backed execution
  -> metrics/alerts/incidents
  -> recovery and release evidence
```

## Verification

```bash
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_connector_certification.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/check_public_business_control_tower.sh
bash scripts/check_public_business_intake_pipeline.sh
bash scripts/check_public_business_task_handoff.sh
bash scripts/check_public_business_notification_channels.sh
bash scripts/check_public_business_context_assistant.sh
bash scripts/check_public_business_action_execution.sh
bash scripts/check_public_business_scenario_replay.sh
bash scripts/check_public_engineering_proof.sh
```

## Boundary

- No production data is included.
- No real Bitrix, bank, accounting, Telegram, email, or payment provider call is
  made by the public demo.
- Provider tokens stay behind `server_secret_store`,
  `private_connector_only`, and `no_browser_token_storage` boundaries.
- Public operation plans use `executionMode: contract_only` and
  `safeToRunAgainstPublicDemo: false`.
