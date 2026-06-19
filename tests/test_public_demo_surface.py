from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "apps/admin/public-demo"


def _demo_data() -> dict[str, object]:
    source = (DEMO_DIR / "demo-data.js").read_text(encoding="utf-8")
    match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", source, flags=re.DOTALL)
    assert match, "demo data assignment not found"
    return json.loads(match.group(1))


def test_public_demo_files_exist() -> None:
    expected = {
        "README.md",
        "index.html",
        "styles.css",
        "demo-data.js",
        "app.js",
    }

    for relative in expected:
        assert (DEMO_DIR / relative).is_file(), relative


def test_public_demo_html_links_static_assets() -> None:
    html = (DEMO_DIR / "index.html").read_text(encoding="utf-8")

    assert "./styles.css" in html
    assert "./demo-data.js" in html
    assert "./app.js" in html
    assert 'data-demo-api-path="/demo/public"' in html
    assert 'id="metricGrid"' in html
    assert 'id="workQueueRows"' in html
    assert 'data-view="workflow"' in html
    assert 'data-view="control"' in html
    assert 'data-view="operations"' in html
    assert 'data-view="incidents"' in html
    assert 'data-view="proof"' in html
    assert 'id="workflowStageRows"' in html
    assert 'id="workflowScenarioRows"' in html
    assert 'id="endToEndScenarioRows"' in html
    assert 'id="endToEndScenarioMeta"' in html
    assert 'id="workflowTimelineRows"' in html
    assert 'id="domainEventRows"' in html
    assert 'id="controlTowerSummaryRows"' in html
    assert 'id="controlTowerProviderRows"' in html
    assert 'id="controlTowerProviderBoundaryRows"' in html
    assert 'id="controlTowerDetectionRows"' in html
    assert 'id="controlTowerDetectionRepairRows"' in html
    assert 'id="controlTowerEscalationRows"' in html
    assert 'id="controlTowerEscalationActionRows"' in html
    assert 'id="controlTowerBriefingRows"' in html
    assert 'id="controlTowerBriefingActionRows"' in html
    assert 'id="controlTowerFlowRows"' in html
    assert 'id="businessIntakeSummaryRows"' in html
    assert 'id="businessIntakeRows"' in html
    assert 'id="businessIntakeWorkbenchRows"' in html
    assert 'id="businessIntakeActionRows"' in html
    assert 'id="businessIntakeBoundaryRows"' in html
    assert 'id="businessTaskSummaryRows"' in html
    assert 'id="businessTaskRows"' in html
    assert 'id="businessTaskOutboxRows"' in html
    assert 'id="businessTaskDraftRows"' in html
    assert 'id="businessTaskBoundaryRows"' in html
    assert 'id="businessNotificationSummaryRows"' in html
    assert 'id="businessNotificationChannelRows"' in html
    assert 'id="businessNotificationDraftRows"' in html
    assert 'id="businessNotificationBoundaryRows"' in html
    assert 'id="businessContextSummaryRows"' in html
    assert 'id="businessContextCardRows"' in html
    assert 'id="businessContextRuleRows"' in html
    assert 'id="businessContextActionRows"' in html
    assert 'id="businessContextBoundaryRows"' in html
    assert 'id="businessActionExecutionSummaryRows"' in html
    assert 'id="businessActionExecutionPlanRows"' in html
    assert 'id="businessActionExecutionPreflightRows"' in html
    assert 'id="businessActionExecutionDryRunRows"' in html
    assert 'id="businessActionExecutionBoundaryRows"' in html
    assert 'id="businessApprovalGatewaySummaryRows"' in html
    assert 'id="businessApprovalGatewayRequestRows"' in html
    assert 'id="businessApprovalGatewayPolicyRows"' in html
    assert 'id="businessApprovalGatewayUnlockRows"' in html
    assert 'id="businessApprovalGatewayBoundaryRows"' in html
    assert 'id="integrationRuntimeSummaryRows"' in html
    assert 'id="integrationRuntimeStepRows"' in html
    assert 'id="integrationRuntimePreflightRows"' in html
    assert 'id="integrationRuntimeOutboxRows"' in html
    assert 'id="integrationRuntimeBoundaryRows"' in html
    assert 'id="integrationExecutionSummaryRows"' in html
    assert 'id="integrationExecutionLedgerRows"' in html
    assert 'id="integrationExecutionTimelineRows"' in html
    assert 'id="integrationExecutionStateRows"' in html
    assert 'id="integrationExecutionRecoveryRows"' in html
    assert 'id="integrationExecutionBoundaryRows"' in html
    assert 'id="controlTowerObservationRows"' in html
    assert 'id="controlTowerExceptionRows"' in html
    assert 'id="controlTowerRepairRows"' in html
    assert 'id="integrationHealthRows"' in html
    assert 'id="adapterStudioSummaryRows"' in html
    assert 'id="adapterStudioFlowRows"' in html
    assert 'id="adapterStudioPlanRows"' in html
    assert 'id="adapterStudioBoundaryRows"' in html
    assert 'id="adapterStudioDiagnosticRows"' in html
    assert 'id="adapterStudioDocRows"' in html
    assert 'id="connectorCertificationSummaryRows"' in html
    assert 'id="connectorCertificationProviderRows"' in html
    assert 'id="connectorCertificationStageRows"' in html
    assert 'id="connectorCertificationGateRows"' in html
    assert 'id="connectorCertificationPathRows"' in html
    assert 'id="connectorCertificationBoundaryRows"' in html
    assert 'id="connectorReplaySummaryRows"' in html
    assert 'id="connectorReplayOutcomeRows"' in html
    assert 'id="connectorReplayBoundaryRows"' in html
    assert 'id="connectorReplayDocRows"' in html
    assert 'id="adapterScenarioRows"' in html
    assert 'id="adapterRows"' in html
    assert 'id="syncJobRows"' in html
    assert 'id="outboxRows"' in html
    assert 'id="recoveryRows"' in html
    assert 'id="alertRoutingSummaryRows"' in html
    assert 'id="alertRouteRows"' in html
    assert 'id="alertBindingRows"' in html
    assert 'id="alertRunbookRows"' in html
    assert 'id="incidentSummaryRows"' in html
    assert 'id="incidentRows"' in html
    assert 'id="incidentTimelineRows"' in html
    assert 'id="incidentActionRows"' in html
    assert 'id="incidentEvidenceRows"' in html
    assert 'id="proofSummaryRows"' in html
    assert 'id="proofGateRows"' in html
    assert 'id="proofEvidenceRows"' in html


def test_public_demo_data_is_synthetic_and_product_shaped() -> None:
    payload = _demo_data()

    assert payload["schemaVersion"] == 1
    assert payload["dataSource"] == "static.fallback"
    assert payload["apiContract"]["path"] == "/demo/public"
    assert payload["apiContract"]["data_profile"] == "synthetic_demo_data"
    assert payload["tenant"]["slug"] == "demo-academy"
    assert payload["tenant"]["status"] == "active"
    assert payload["workflow"]["id"] == "wf-demo-lead-to-student"
    assert payload["workflow"]["currentStage"] == "student_sync"
    assert len(payload["workflow"]["stages"]) >= 5
    assert len(payload["workflowScenarios"]) >= 3
    scenario_by_id = {scenario["id"]: scenario for scenario in payload["workflowScenarios"]}
    assert set(scenario_by_id) >= {
        "scenario-contract-approval-sync",
        "scenario-signature-task",
        "scenario-accounting-export",
    }
    assert {scenario["actionType"] for scenario in payload["workflowScenarios"]} >= {
        "emit_outbox_event",
        "create_task_record",
        "request_adapter_sync",
    }
    assert {
        output
        for scenario in payload["workflowScenarios"]
        for output in scenario["outputs"]
    } >= {
        "audit_event",
        "outbox_event",
        "task_record",
        "integration_job",
        "action_run",
    }
    assert scenario_by_id["scenario-contract-approval-sync"]["trigger"] == (
        "business_record.status_changed contract:draft->approved"
    )
    assert scenario_by_id["scenario-signature-task"]["evidence"] == "workflow.task_record.created"
    assert scenario_by_id["scenario-accounting-export"]["status"] == "pending"
    assert payload["endToEndScenario"]["id"] == "scenario-approval-notification-adapter-incident"
    assert payload["endToEndScenario"]["status"] == "reviewable"
    assert payload["endToEndScenario"]["currentStep"] == "incident_resolved"
    assert len(payload["endToEndScenario"]["chain"]) >= 6
    assert {step["step"] for step in payload["endToEndScenario"]["chain"]} >= {
        "approval",
        "notification",
        "adapter",
        "incident",
        "recovery",
        "proof",
    }
    assert {step["evidence"] for step in payload["endToEndScenario"]["chain"]} >= {
        "workflow.contract_approved",
        "notification.manager_signature_task.created",
        "integration.accounting_export.requested",
        "integration.incident.status_changed",
        "postcheck.gates.passed",
        "docs/public/ENGINEERING_PROOF.md",
    }
    assert set(payload["endToEndScenario"]["proof"]) >= {
        "workflow.contract_approved",
        "notification.manager_signature_task.created",
        "integration.accounting_export.requested",
        "integration.incident.status_changed",
        "postcheck.gates.passed",
        "docs/public/ENGINEERING_PROOF.md",
    }
    control_tower = payload["businessControlTower"]
    assert {item["label"] for item in control_tower["summary"]} >= {
        "Observed systems",
        "Open exceptions",
        "Repair actions",
        "External writes",
        "Provider intake",
    }
    assert control_tower["providerIntake"]["providerKey"] == "crm.bitrix24.mock"
    assert control_tower["providerIntake"]["sourceType"] == "crm_deal"
    assert control_tower["providerIntake"]["status"] == "mapped"
    assert control_tower["providerIntake"]["safePayload"] == {
        "amount_bucket": "1000-2000",
        "owner_role": "sales",
        "source_state": "invoice_sent",
    }
    assert set(control_tower["providerIntake"]["droppedKeys"]) >= {
        "access_token",
        "full_name",
        "phone",
    }
    assert control_tower["providerIntake"]["normalizedObservation"]["wouldCreate"] == (
        "BusinessStateObservation"
    )
    assert control_tower["providerIntake"]["normalizedObservation"]["wouldRecordEvent"] == (
        "business_state.observation.recorded"
    )
    assert {
        control_tower["providerIntake"]["normalizedObservation"]["rawPayloadIncluded"],
        control_tower["providerIntake"]["normalizedObservation"]["piiIncluded"],
        control_tower["providerIntake"]["normalizedObservation"]["externalFetch"],
        control_tower["providerIntake"]["normalizedObservation"]["externalMutation"],
        control_tower["providerIntake"]["normalizedObservation"]["requiresSecret"],
    } == {False}
    assert {item["name"] for item in control_tower["providerIntake"]["dataBoundaries"]} == {
        "preview_only_no_persist",
        "raw_provider_payload_not_returned",
        "secret_boundary",
    }
    assert {item["step"] for item in control_tower["providerIntake"]["nextSteps"]} == {
        "record_normalized_observation",
        "open_workbench_context",
        "run_detection_preview",
    }
    assert {item["externalMutation"] for item in control_tower["providerIntake"]["nextSteps"]} == {
        False
    }
    assert control_tower["providerIntake"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-provider-intake/preview"
    )
    assert control_tower["detection"]["ruleSet"] == "payment_reconciliation"
    assert control_tower["detection"]["status"] == "detected"
    assert {item["type"] for item in control_tower["detection"]["detectedExceptions"]} == {
        "crm_payment_mismatch"
    }
    assert {item["action"] for item in control_tower["detection"]["suggestedRepairActions"]} == {
        "sync_status"
    }
    assert {item["externalMutation"] for item in control_tower["detection"]["suggestedRepairActions"]} == {False}
    assert control_tower["detection"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-detections/preview"
    )
    assert control_tower["workbenchContext"]["contextKind"] == "role_assist"
    assert control_tower["workbenchContext"]["role"] == "accountant"
    assert control_tower["workbenchContext"]["riskLevel"] == "attention"
    assert set(control_tower["workbenchContext"]["sourceSystems"]) >= {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert {item["systemFamily"] for item in control_tower["workbenchContext"]["contextCards"]} == {
        "accounting",
        "bank",
        "crm",
    }
    assert {item["piiIncluded"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}
    assert {item["rawPayloadIncluded"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}
    assert {item["externalFetch"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}
    assert {item["externalMutation"] for item in control_tower["workbenchContext"]["contextCards"]} == {False}
    assert {item["action"] for item in control_tower["workbenchContext"]["suggestedActions"]} >= {
        "reconcile_crm_payment_status",
        "review_accounting_export",
        "open_action_plan_preview",
    }
    assert {item["externalMutation"] for item in control_tower["workbenchContext"]["suggestedActions"]} == {
        False
    }
    assert {item["name"] for item in control_tower["workbenchContext"]["dataBoundaries"]} == {
        "read_only_source_context",
        "pii_redaction",
        "secret_boundary",
    }
    assert control_tower["workbenchContext"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-workbench-context/preview"
    )
    assert control_tower["escalation"]["policy"] == "exception_triage"
    assert control_tower["escalation"]["riskLevel"] == "attention"
    assert {item["queue"] for item in control_tower["escalation"]["queues"]} == {
        "finance_reconciliation"
    }
    assert {item["ownerRole"] for item in control_tower["escalation"]["queues"]} == {"accountant"}
    assert {item["minSlaMinutes"] for item in control_tower["escalation"]["queues"]} == {120}
    assert {item["nextAction"] for item in control_tower["escalation"]["items"]} == {
        "execute_repair_dry_run"
    }
    assert {item["externalMutation"] for item in control_tower["escalation"]["items"]} == {False}
    assert {item["action"] for item in control_tower["escalation"]["suggestedActions"]} == {
        "execute_repair_dry_run"
    }
    assert control_tower["escalation"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-escalations/preview"
    )
    assert control_tower["actionPlan"]["planKind"] == "exception_resolution"
    assert control_tower["actionPlan"]["role"] == "accountant"
    assert control_tower["actionPlan"]["riskLevel"] == "attention"
    assert {item["lane"] for item in control_tower["actionPlan"]["lanes"]} == {
        "finance_reconciliation"
    }
    assert [item["step"] for item in control_tower["actionPlan"]["steps"]] == [
        "verify_source_evidence",
        "execute_repair_dry_run",
        "close_or_acknowledge_exception",
    ]
    assert {item["externalMutation"] for item in control_tower["actionPlan"]["steps"]} == {False}
    assert {item["name"] for item in control_tower["actionPlan"]["automationCandidates"]} >= {
        "queue_repair_execution",
        "recheck_accounting_export",
    }
    assert {item["status"] for item in control_tower["actionPlan"]["approvalGates"]} == {"satisfied"}
    assert control_tower["actionPlan"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-action-plans/preview"
    )
    assert control_tower["notifications"]["notificationKind"] == "action_plan_updates"
    assert control_tower["notifications"]["role"] == "accountant"
    assert control_tower["notifications"]["riskLevel"] == "attention"
    assert {item["channel"] for item in control_tower["notifications"]["channels"]} == {
        "in_app",
        "telegram",
    }
    assert {item["externalDelivery"] for item in control_tower["notifications"]["channels"]} == {False}
    assert {item["requiresSecret"] for item in control_tower["notifications"]["channels"]} == {False, True}
    assert {item["piiIncluded"] for item in control_tower["notifications"]["drafts"]} == {False}
    assert {item["externalDelivery"] for item in control_tower["notifications"]["drafts"]} == {False}
    assert {item["sendMode"] for item in control_tower["notifications"]["deliveryPlan"]} == {"preview_only"}
    assert {item["wouldEnqueueEvent"] for item in control_tower["notifications"]["deliveryPlan"]} == {
        "notification.delivery.requested"
    }
    assert {item["name"] for item in control_tower["notifications"]["approvalGates"]} >= {
        "notification_content_review",
        "repair_action_approval",
    }
    assert control_tower["notifications"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-notifications/preview"
    )
    assert control_tower["briefing"]["role"] == "accountant"
    assert control_tower["briefing"]["riskLevel"] == "attention"
    assert set(control_tower["briefing"]["sourceSystems"]) >= {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert {item["type"] for item in control_tower["briefing"]["highlights"]} >= {
        "business_exception",
        "state_observation",
        "repair_context",
    }
    assert {item["action"] for item in control_tower["briefing"]["recommendedActions"]} >= {
        "execute_repair_dry_run",
        "review_accounting_export",
    }
    assert control_tower["briefing"]["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-briefings/preview"
    )
    assert {observation["system"] for observation in control_tower["observations"]} >= {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert {business_exception["type"] for business_exception in control_tower["exceptions"]} == {
        "crm_payment_mismatch"
    }
    assert {repair_action["action"] for repair_action in control_tower["repairActions"]} == {"sync_status"}
    assert {repair_action["externalMutation"] for repair_action in control_tower["repairActions"]} == {False}
    assert {step["step"] for step in control_tower["flow"]} >= {
        "intake",
        "observe",
        "detect",
        "propose",
        "approve",
        "context",
        "plan",
        "notify",
        "execute",
    }
    assert set(control_tower["metrics"]) >= {
        "drivedesk_business_state_observations",
        "drivedesk_business_exceptions",
        "drivedesk_repair_actions",
    }
    assert control_tower["api"]["observe"] == "POST /tenants/{tenant_id}/business-state/observations"
    assert control_tower["api"]["execute"] == "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute"
    assert len(payload["timeline"]) >= 5
    assert len(payload["domainEvents"]) >= 4
    assert {event["event"] for event in payload["domainEvents"]} >= {
        "lead.created",
        "student.created",
        "contract.generated",
        "student.sync.requested",
    }
    assert len(payload["metrics"]) >= 4
    assert len(payload["workQueue"]) >= 4
    assert len(payload["members"]) >= 3
    assert len(payload["auditEvents"]) >= 3
    assert len(payload["adapters"]) >= 3
    adapter_by_key = {adapter["key"]: adapter for adapter in payload["adapters"]}
    assert adapter_by_key["file.import.fake"]["supportedConnectionScopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    assert adapter_by_key["file.import.fake"]["defaultConnectionScopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    file_import_operations = {
        operation["key"]: operation
        for operation in adapter_by_key["file.import.fake"]["operationContracts"]
    }
    assert file_import_operations["file_import_preview"]["requiredConnectionScope"] == "file_import:preview"
    assert file_import_operations["file_import_execute"]["requiredConnectionScope"] == "file_import:execute"
    assert file_import_operations["file_import_execute"]["eventType"] == "integration.file_import.requested"
    assert file_import_operations["file_import_execute"]["idempotencyKeys"] == [
        "tenant_id",
        "source_name",
        "source_format",
        "records_hash",
    ]
    assert adapter_by_key["accounting.export.mock"]["status"] == "active"
    assert adapter_by_key["accounting.export.mock"]["supportedConnectionScopes"] == ["accounting:export"]
    assert adapter_by_key["accounting.export.mock"]["defaultConnectionScopes"] == ["accounting:export"]
    accounting_operations = {
        operation["key"]: operation
        for operation in adapter_by_key["accounting.export.mock"]["operationContracts"]
    }
    assert accounting_operations["accounting_export_execute"]["eventType"] == "accounting.export.requested"
    assert accounting_operations["accounting_export_execute"]["requiredConnectionScope"] == "accounting:export"
    assert accounting_operations["accounting_export_execute"]["endpoint"] == (
        "POST /tenants/{tenant_id}/integration-exports/accounting"
    )
    assert adapter_by_key["crm.bitrix24.mock"]["status"] == "active"
    assert adapter_by_key["crm.bitrix24.mock"]["supportedConnectionScopes"] == [
        "crm:deal.ingest",
        "crm:deal.preview",
    ]
    crm_auth = adapter_by_key["crm.bitrix24.mock"]["authProfile"]
    assert crm_auth["mode"] == "oauth2_or_webhook_boundary"
    assert crm_auth["publicDemoRequiresSecret"] is False
    assert crm_auth["realProviderRequiresSecret"] is True
    assert crm_auth["credentialPlacement"] == "server_secret_store"
    assert crm_auth["tokenExchange"] == "private_connector_only"
    assert "no_browser_token_storage" in crm_auth["dataBoundaries"]
    crm_operations = {
        operation["key"]: operation
        for operation in adapter_by_key["crm.bitrix24.mock"]["operationContracts"]
    }
    assert crm_operations["crm_deal_intake_preview"]["eventType"] == "business_provider_intake.previewed"
    assert crm_operations["crm_deal_intake_preview"]["requiredConnectionScope"] == "crm:deal.preview"
    assert crm_operations["crm_deal_ingest_execute"]["eventType"] == "integration.crm_deal.ingest.requested"
    assert crm_operations["crm_deal_ingest_execute"]["requiredConnectionScope"] == "crm:deal.ingest"
    assert len(payload["adapterScenarios"]) >= 4
    adapter_scenario_by_id = {scenario["id"]: scenario for scenario in payload["adapterScenarios"]}
    assert set(adapter_scenario_by_id) >= {
        "adapter-crm-deal-ingest",
        "adapter-crm-deal-preview",
        "adapter-file-import-preview",
        "adapter-file-import-execute",
        "adapter-accounting-export-retry",
        "adapter-dead-letter-review",
    }
    assert {scenario["phase"] for scenario in payload["adapterScenarios"]} >= {
        "preview",
        "execute",
        "retry",
        "operator_review",
    }
    assert {scenario["adapter"] for scenario in payload["adapterScenarios"]} >= {
        "crm.bitrix24.mock",
        "file.import.fake",
        "accounting.export.mock",
    }
    assert {scenario["requiredScope"] for scenario in payload["adapterScenarios"]} >= {
        "crm:deal.ingest",
        "crm:deal.preview",
        "file_import:preview",
        "file_import:execute",
        "accounting:export",
    }
    assert {
        output
        for scenario in payload["adapterScenarios"]
        for output in scenario["outputs"]
    } >= {
        "normalized_observation",
        "redaction_evidence",
        "safe_payload",
        "mapping_preview",
        "outbox_event",
        "adapter_job",
        "retry_scheduled",
        "review_card",
        "manual_retry_endpoint",
    }
    assert adapter_scenario_by_id["adapter-file-import-preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/integration-mapping-preview"
    )
    assert adapter_scenario_by_id["adapter-crm-deal-preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/business-provider-intake/preview"
    )
    assert adapter_scenario_by_id["adapter-crm-deal-ingest"]["operation"] == "crm_deal_ingest_execute"
    assert adapter_scenario_by_id["adapter-accounting-export-retry"]["status"] == "retry"
    assert adapter_scenario_by_id["adapter-dead-letter-review"]["status"] == "dead_letter"
    adapter_studio = payload["adapterStudio"]
    assert {item["label"] for item in adapter_studio["summary"]} >= {
        "SDK plans",
        "CRM preview",
        "Worker ingest",
        "Secrets",
    }
    assert {item["evidence"] for item in adapter_studio["flow"]} >= {
        "GET /integration-adapters",
        "sdk/generated/public-demo/",
        "business_provider_intake.previewed",
        "integration.crm_deal.ingest.requested",
        "drivedesk_integration_incidents",
    }
    studio_plans = {item["scenarioId"]: item for item in adapter_studio["operationPlans"]}
    assert set(studio_plans) == {"adapter-crm-deal-preview", "adapter-crm-deal-ingest"}
    assert studio_plans["adapter-crm-deal-preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/business-provider-intake/preview"
    )
    assert studio_plans["adapter-crm-deal-preview"]["executionMode"] == "contract_only"
    assert studio_plans["adapter-crm-deal-preview"]["safeToRunAgainstPublicDemo"] is False
    assert studio_plans["adapter-crm-deal-ingest"]["method"] == "WORKER"
    assert studio_plans["adapter-crm-deal-ingest"]["endpoint"] == (
        "worker:drivedesk_worker.main.process_pending_outbox"
    )
    assert {item["evidence"] for item in adapter_studio["boundaries"]} >= {
        "server_secret_store",
        "private_connector_only",
        "redaction_evidence",
        "safeToRunAgainstPublicDemo=false",
    }
    assert {item["metric"] for item in adapter_studio["diagnostics"]} >= {
        "drivedesk_integration_connection_checks",
        "drivedesk_integration_reconciliations",
        "drivedesk_integration_incidents",
        "integration.operator_review.created",
    }
    assert {item["path"] for item in adapter_studio["docs"]} >= {
        "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
        "docs/public/CLIENT_SDK.md",
        "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
    }
    connector_certification = payload["connectorCertification"]
    assert connector_certification["status"] == "validated"
    assert connector_certification["command"] == "GET /demo/connector-certification"
    assert connector_certification["certificationLevel"] == "public_contract_certified"
    assert connector_certification["adapterCount"] >= 3
    assert connector_certification["privateReadyCount"] >= 2
    provider_profiles = {
        item["adapterKey"]: item for item in connector_certification["providerProfiles"]
    }
    assert {"crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"}.issubset(
        provider_profiles
    )
    assert provider_profiles["crm.bitrix24.mock"]["serverSecretBoundary"] is True
    assert provider_profiles["crm.bitrix24.mock"]["readyForPrivateConnector"] is True
    assert {item["stage"] for item in connector_certification["certificationStages"]} >= {
        "provider_profile",
        "capability_manifest",
        "auth_boundary",
        "fixture_replay",
        "runtime_preview",
        "execution_timeline",
        "release_gate",
    }
    assert {item["gate"] for item in connector_certification["certificationGates"]} == {
        "no_real_provider_call",
        "no_secret_value",
        "no_raw_payload",
        "idempotent_execution",
        "operator_review",
    }
    assert {item["externalMutation"] for item in connector_certification["certificationGates"]} == {
        False
    }
    assert {item["name"] for item in connector_certification["dataBoundaries"]} == {
        "public_demo_data",
        "browser_boundary",
        "private_connector_boundary",
    }
    connector_replay = payload["connectorFixtureReplay"]
    assert connector_replay["status"] == "validated"
    assert connector_replay["command"] == "bash scripts/check_public_connector_fixture_replay.sh"
    assert connector_replay["fixtureFile"] == "examples/connector-fixtures/replay-fixtures.sanitized.json"
    assert connector_replay["evidenceFile"] == "docs/public/evidence/connector-fixture-replay.sanitized.json"
    assert {item["label"] for item in connector_replay["summary"]} >= {
        "Fixture groups",
        "Provider calls",
        "Secrets",
        "Operator path",
    }
    replay_outcomes = {item["group"]: item for item in connector_replay["outcomes"]}
    assert set(replay_outcomes) == {
        "happy_path_preview",
        "sensitive_payload_redaction",
        "invalid_payload",
        "retryable_provider_failure",
        "dead_letter_provider_failure",
        "reconciliation_mismatch",
    }
    assert replay_outcomes["happy_path_preview"]["evidence"] == "safe_payload_present=true"
    assert replay_outcomes["sensitive_payload_redaction"]["evidence"] == "redaction_evidence_present=true"
    assert replay_outcomes["invalid_payload"]["evidence"] == "outbox_event_created=false"
    assert replay_outcomes["retryable_provider_failure"]["status"] == "retry_scheduled"
    assert replay_outcomes["dead_letter_provider_failure"]["evidence"] == "integration.operator_review.created"
    assert replay_outcomes["reconciliation_mismatch"]["evidence"] == "drivedesk_integration_reconciliations"
    assert {item["state"] for item in connector_replay["boundaries"]} >= {
        "not_returned",
        "disabled",
    }
    assert {item["path"] for item in connector_replay["docs"]} >= {
        "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
        "docs/public/evidence/connector-fixture-replay.sanitized.json",
        "examples/connector-fixtures/replay-fixtures.sanitized.json",
    }
    intake_pipeline = payload["businessIntakePipeline"]
    assert intake_pipeline["status"] == "previewed"
    assert intake_pipeline["command"] == "POST /tenants/{tenant_id}/business-intake-pipeline/preview"
    assert {item["label"] for item in intake_pipeline["summary"]} >= {
        "Provider events",
        "Dropped unsafe keys",
        "Detected exceptions",
        "External writes",
    }
    assert intake_pipeline["sourceSystems"] == [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    ]
    assert {item["providerKey"] for item in intake_pipeline["intakePreviews"]} == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert {"access_token", "full_name", "phone"} <= set(intake_pipeline["intakePreviews"][0]["droppedKeys"])
    assert {item["systemFamily"] for item in intake_pipeline["workbench"]["contextCards"]} == {
        "accounting",
        "bank",
        "crm",
    }
    assert {item["rawPayloadIncluded"] for item in intake_pipeline["workbench"]["contextCards"]} == {False}
    assert {item["piiIncluded"] for item in intake_pipeline["workbench"]["contextCards"]} == {False}
    assert {item["externalMutation"] for item in intake_pipeline["workbench"]["contextCards"]} == {False}
    assert intake_pipeline["detections"]["status"] == "detected"
    assert intake_pipeline["detections"]["detectedExceptions"][0]["exceptionType"] == "crm_payment_mismatch"
    assert intake_pipeline["detections"]["suggestedRepairActions"][0]["requiresApproval"] is True
    assert {item["externalMutation"] for item in intake_pipeline["actionPlan"]["steps"]} == {False}
    assert {item["gate"] for item in intake_pipeline["actionPlan"]["approvalGates"]} == {
        "external_write_gate",
        "notification_delivery_gate",
    }
    assert intake_pipeline["notifications"]["externalDelivery"] is False
    assert intake_pipeline["notifications"]["containsPii"] is False
    assert {item["name"] for item in intake_pipeline["dataBoundaries"]} == {
        "no_external_calls",
        "no_persistence",
        "secret_and_pii_boundary",
    }
    assert {item["path"] for item in intake_pipeline["docs"]} >= {
        "docs/public/BUSINESS_INTAKE_PIPELINE.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/API_BACKED_DEMO.md",
    }
    task_handoff = payload["businessTaskHandoff"]
    assert task_handoff["status"] == "previewed"
    assert task_handoff["command"] == "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    assert {item["label"] for item in task_handoff["summary"]} >= {
        "Task cards",
        "Internal outbox",
        "Draft notifications",
        "External writes",
    }
    assert task_handoff["role"] == "accountant"
    assert task_handoff["subject"] == "deal:DEAL-2026-001"
    assert {item["status"] for item in task_handoff["taskCards"]} == {"would_create"}
    assert {item["wouldCreate"] for item in task_handoff["taskCards"]} == {"BusinessRecord(type=task)"}
    assert {item["externalMutation"] for item in task_handoff["taskCards"]} == {False}
    assert {item["containsPii"] for item in task_handoff["taskCards"]} == {False}
    assert {item["rawPayloadIncluded"] for item in task_handoff["taskCards"]} == {False}
    assert {item["eventType"] for item in task_handoff["outboxCandidates"]} == {"task.created"}
    assert {item["adapterKey"] for item in task_handoff["outboxCandidates"]} == {"internal.noop"}
    assert {item["status"] for item in task_handoff["outboxCandidates"]} == {"would_enqueue"}
    assert {item["externalMutation"] for item in task_handoff["outboxCandidates"]} == {False}
    assert {item["status"] for item in task_handoff["notificationDrafts"]} == {"draft_only"}
    assert {item["externalDelivery"] for item in task_handoff["notificationDrafts"]} == {False}
    assert {item["containsPii"] for item in task_handoff["notificationDrafts"]} == {False}
    assert {item["gate"] for item in task_handoff["approvalGates"]} == {
        "task_creation_review",
        "external_write_gate",
        "repair_action_approval",
    }
    assert {item["name"] for item in task_handoff["dataBoundaries"]} == {
        "preview_only_no_persistence",
        "internal_only_outbox",
        "safe_task_payload",
    }
    assert {item["path"] for item in task_handoff["docs"]} >= {
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/WORKFLOW_DEMO.md",
        "docs/public/BUSINESS_INTAKE_PIPELINE.md",
    }
    notification_channels = payload["businessNotificationChannels"]
    assert notification_channels["status"] == "previewed"
    assert (
        notification_channels["command"]
        == "POST /tenants/{tenant_id}/business-notification-channels/preview"
    )
    assert {item["label"] for item in notification_channels["summary"]} >= {
        "Channels",
        "Internal ready",
        "Draft-only external",
        "External deliveries",
    }
    assert notification_channels["role"] == "accountant"
    assert notification_channels["subject"] == "deal:DEAL-2026-001"
    channel_by_key = {item["channel"]: item for item in notification_channels["channels"]}
    assert set(channel_by_key) == {"in_app", "telegram", "email", "sms", "webhook"}
    assert channel_by_key["in_app"]["status"] == "ready"
    assert channel_by_key["in_app"]["configured"] is True
    assert channel_by_key["in_app"]["requiresSecret"] is False
    assert channel_by_key["in_app"]["requiresPrivateConnector"] is False
    assert {
        channel_by_key[channel]["requiresSecret"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {
        channel_by_key[channel]["requiresPrivateConnector"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {item["externalDelivery"] for item in notification_channels["channels"]} == {False}
    assert {item["containsPii"] for item in notification_channels["channels"]} == {False}
    assert {item["rawPayloadIncluded"] for item in notification_channels["channels"]} == {False}
    assert {item["rule"] for item in notification_channels["routingRules"]} == {
        "prefer_internal_in_app",
        "external_channels_require_private_connector",
        "safe_payload_only",
    }
    assert len(notification_channels["deliveryDrafts"]) == 5
    assert {item["wouldEnqueueEvent"] for item in notification_channels["deliveryDrafts"]} == {
        "notification.delivery.requested"
    }
    assert {item["externalDelivery"] for item in notification_channels["deliveryDrafts"]} == {
        False
    }
    assert {item["containsPii"] for item in notification_channels["deliveryDrafts"]} == {False}
    assert {item["rawPayloadIncluded"] for item in notification_channels["deliveryDrafts"]} == {
        False
    }
    assert {item["gate"] for item in notification_channels["approvalGates"]} == {
        "notification_content_review",
        "private_channel_secret_setup",
        "external_delivery_gate",
    }
    assert {item["name"] for item in notification_channels["dataBoundaries"]} == {
        "preview_only_no_delivery",
        "server_secret_store_boundary",
        "safe_notification_payload",
    }
    assert {item["path"] for item in notification_channels["docs"]} >= {
        "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/API_BACKED_DEMO.md",
    }
    context_assistant = payload["businessContextAssistant"]
    assert context_assistant["status"] == "previewed"
    assert (
        context_assistant["command"]
        == "POST /tenants/{tenant_id}/business-workbench-context/preview"
    )
    assert {item["label"] for item in context_assistant["summary"]} >= {
        "Context cards",
        "Source systems",
        "Suggested actions",
        "External writes",
    }
    assert context_assistant["role"] == "accountant"
    assert context_assistant["subject"] == "deal:DEAL-2026-001"
    assert set(context_assistant["sourceSystems"]) == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
        "legal.reference.mock",
    }
    assert {item["systemFamily"] for item in context_assistant["contextCards"]} == {
        "crm",
        "bank",
        "accounting",
        "legal",
    }
    assert {item["externalFetch"] for item in context_assistant["contextCards"]} == {False}
    assert {item["externalMutation"] for item in context_assistant["contextCards"]} == {False}
    assert {item["containsPii"] for item in context_assistant["contextCards"]} == {False}
    assert {item["rawPayloadIncluded"] for item in context_assistant["contextCards"]} == {False}
    assert {
        item.get("fullTextIncluded", False)
        for item in context_assistant["contextCards"]
        if item["systemFamily"] == "legal"
    } == {False}
    assert {item["rule"] for item in context_assistant["insightRules"]} == {
        "correlate_payment_evidence",
        "detect_accounting_export_gap",
        "attach_policy_reference",
    }
    assert {item["externalMutation"] for item in context_assistant["insightRules"]} == {False}
    assert {item["action"] for item in context_assistant["suggestedActions"]} == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "attach_policy_reference",
        "prepare_internal_notification",
    }
    assert {item["externalMutation"] for item in context_assistant["suggestedActions"]} == {
        False
    }
    assert {item["name"] for item in context_assistant["dataBoundaries"]} == {
        "read_only_context_preview",
        "no_raw_provider_payload",
        "secret_boundary",
        "legal_reference_link_only",
    }
    assert context_assistant["api"]["standalone"] == "GET /demo/business-context-assistant"
    assert context_assistant["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-workbench-context/preview"
    )
    assert {item["path"] for item in context_assistant["docs"]} >= {
        "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
    }
    action_execution = payload["businessActionExecution"]
    assert action_execution["status"] == "previewed"
    assert (
        action_execution["command"]
        == "POST /tenants/{tenant_id}/business-action-executions/preview"
    )
    assert {item["label"] for item in action_execution["summary"]} >= {
        "Execution plans",
        "Preflight checks",
        "Approval gates",
        "External writes",
    }
    assert action_execution["role"] == "accountant"
    assert action_execution["subject"] == "deal:DEAL-2026-001"
    assert {item["action"] for item in action_execution["executionPlan"]} == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "prepare_internal_notification",
    }
    assert {item["dryRun"] for item in action_execution["executionPlan"]} == {True}
    assert {item["externalMutation"] for item in action_execution["executionPlan"]} == {False}
    assert {item["containsPii"] for item in action_execution["executionPlan"]} == {False}
    assert {item["rawPayloadIncluded"] for item in action_execution["executionPlan"]} == {False}
    assert {item["safePayloadProfile"] for item in action_execution["executionPlan"]} == {
        "role_subject_action_reference"
    }
    assert all(
        item["idempotencyKey"].startswith("business-action-execution:")
        for item in action_execution["executionPlan"]
    )
    assert any(item["commitWouldMutateProvider"] for item in action_execution["executionPlan"])
    assert any(item["safeToAutoRun"] is False for item in action_execution["executionPlan"])
    assert {item["check"] for item in action_execution["preflightChecks"]} == {
        "safe_payload_profile",
        "idempotency_key_ready",
        "approval_gate_attached",
        "connector_secret_boundary",
    }
    assert {item["wouldRecord"] for item in action_execution["dryRunResults"]} == {
        "WorkflowActionRun"
    }
    assert {item["status"] for item in action_execution["dryRunResults"]} == {"would_enqueue"}
    assert {item["externalMutation"] for item in action_execution["dryRunResults"]} == {False}
    assert {item["gate"] for item in action_execution["approvalGates"]} == {
        "operator_review_gate",
        "external_write_gate",
        "idempotent_outbox_gate",
    }
    assert {item["step"] for item in action_execution["rollbackPlan"]} == {
        "preview_has_no_rollback",
        "commit_uses_outbox_recovery",
    }
    assert {item["name"] for item in action_execution["dataBoundaries"]} == {
        "dry_run_only",
        "no_provider_write",
        "safe_execution_payload",
        "audit_and_outbox_contract",
    }
    assert action_execution["api"]["standalone"] == "GET /demo/business-action-execution"
    assert action_execution["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-action-executions/preview"
    )
    assert {item["path"] for item in action_execution["docs"]} >= {
        "docs/public/BUSINESS_ACTION_EXECUTION.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
    }
    approval_gateway = payload["businessApprovalGateway"]
    assert approval_gateway["status"] == "previewed"
    assert (
        approval_gateway["command"]
        == "POST /tenants/{tenant_id}/business-approval-gateway/preview"
    )
    assert {item["label"] for item in approval_gateway["summary"]} >= {
        "Approval requests",
        "Policy checks",
        "Commit unlocks",
        "Provider writes",
    }
    assert approval_gateway["role"] == "accountant"
    assert approval_gateway["subject"] == "deal:DEAL-2026-001"
    assert {item["action"] for item in approval_gateway["approvalRequests"]} == {
        "queue_accounting_export_after_review",
    }
    assert {item["requiresDualControl"] for item in approval_gateway["approvalRequests"]} == {
        True
    }
    assert {
        item["commitWouldMutateProvider"] for item in approval_gateway["approvalRequests"]
    } == {True}
    assert {item["externalMutation"] for item in approval_gateway["approvalRequests"]} == {
        False
    }
    assert all(
        item["idempotencyKey"].startswith("business-approval-gateway:")
        for item in approval_gateway["approvalRequests"]
    )
    assert all(
        item["sourceIdempotencyKey"].startswith("business-action-execution:")
        for item in approval_gateway["approvalRequests"]
    )
    assert {item["check"] for item in approval_gateway["policyChecks"]} == {
        "rbac_approver_role",
        "dual_control_required",
        "idempotency_preserved",
        "provider_write_closed_until_approval",
    }
    assert {item["route"] for item in approval_gateway["approverRouting"]} == {
        "owner_or_accountant_review",
        "escalate_if_sla_missed",
    }
    assert {item["wouldRecord"] for item in approval_gateway["commitUnlocks"]} == {
        "WorkflowActionRun"
    }
    assert {item["providerWriteUnlocked"] for item in approval_gateway["commitUnlocks"]} == {
        False
    }
    assert {item["event"] for item in approval_gateway["auditTrail"]} == {
        "business_approval.requested",
        "business_approval.policy_checked",
        "business_approval.commit_unlocked",
    }
    assert {item["name"] for item in approval_gateway["dataBoundaries"]} == {
        "preview_only_no_approval_record",
        "provider_write_locked",
        "rbac_dual_control",
        "safe_approval_payload",
    }
    assert approval_gateway["api"]["standalone"] == "GET /demo/business-approval-gateway"
    assert approval_gateway["api"]["preview"] == (
        "POST /tenants/{tenant_id}/business-approval-gateway/preview"
    )
    assert {item["path"] for item in approval_gateway["docs"]} >= {
        "docs/public/BUSINESS_APPROVAL_GATEWAY.md",
        "docs/public/BUSINESS_ACTION_EXECUTION.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
    }
    integration_runtime = payload["integrationRuntime"]
    assert integration_runtime["status"] == "previewed"
    assert integration_runtime["command"] == "POST /tenants/{tenant_id}/integration-runtime/preview"
    assert integration_runtime["adapterKey"] == "accounting.export.mock"
    assert integration_runtime["operationKey"] == "accounting_export_execute"
    assert integration_runtime["executionMode"] == "contract_only"
    assert {item["label"] for item in integration_runtime["summary"]} >= {
        "Runtime steps",
        "Adapter",
        "Outbox",
        "Provider calls",
    }
    assert integration_runtime["operationContract"]["eventType"] == "accounting.export.requested"
    assert integration_runtime["operationContract"]["requiredConnectionScope"] == "accounting:export"
    assert {item["step"] for item in integration_runtime["runtimeSteps"]} >= {
        "contract_selected",
        "scope_preflight",
        "idempotency_prepared",
        "approval_dependency",
        "outbox_handoff",
        "worker_boundary",
        "reconciliation_plan",
    }
    assert {item["check"] for item in integration_runtime["preflightChecks"]} == {
        "adapter_registered",
        "operation_contract_present",
        "required_scope_available",
        "idempotency_keys_declared",
        "secret_boundary_server_side",
        "provider_write_disabled_in_preview",
    }
    assert integration_runtime["outboxHandoff"]["wouldEnqueueEvent"] == "accounting.export.requested"
    assert integration_runtime["outboxHandoff"]["providerCallEnabled"] is False
    assert integration_runtime["workerBoundary"]["publicRunMode"] == "contract_only"
    assert integration_runtime["workerBoundary"]["providerCallEnabled"] is False
    assert {item["route"] for item in integration_runtime["incidentRoutes"]} == {
        "retry_queue",
        "dead_letter_review",
        "reconciliation_mismatch",
    }
    assert {item["name"] for item in integration_runtime["dataBoundaries"]} == {
        "contract_only_preview",
        "server_side_secret_boundary",
        "safe_payload_boundary",
        "approval_before_provider_write",
    }
    assert integration_runtime["api"]["standalone"] == "GET /demo/integration-runtime"
    assert integration_runtime["api"]["preview"] == (
        "POST /tenants/{tenant_id}/integration-runtime/preview"
    )
    assert {item["path"] for item in integration_runtime["docs"]} >= {
        "docs/public/INTEGRATION_RUNTIME.md",
        "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
        "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
    }
    integration_execution = payload["integrationExecution"]
    assert integration_execution["status"] == "previewed"
    assert (
        integration_execution["command"]
        == "POST /tenants/{tenant_id}/integration-executions/preview"
    )
    assert integration_execution["adapterKey"] == "accounting.export.mock"
    assert integration_execution["operationKey"] == "accounting_export_execute"
    assert integration_execution["executionMode"] == "contract_only"
    assert {item["label"] for item in integration_execution["summary"]} >= {
        "Timeline",
        "Run ledger",
        "Provider calls",
        "Recovery",
    }
    assert integration_execution["runLedger"]["wouldCreateWorkflowActionRun"] is True
    assert integration_execution["runLedger"]["wouldCreateOutboxEvent"] is True
    assert integration_execution["runLedger"]["wouldCallProvider"] is False
    assert integration_execution["runLedger"]["evidence"] == "integration_execution.run_ledger_prepared"
    assert [item["stage"] for item in integration_execution["timeline"]] == [
        "request_accepted",
        "runtime_preflight",
        "approval_gate",
        "outbox_enqueue",
        "worker_dispatch",
        "provider_call",
        "reconciliation",
        "operator_closure",
    ]
    assert {item["name"] for item in integration_execution["retryPolicy"]} == {
        "retry_queue",
        "dead_letter_review",
    }
    assert {item["name"] for item in integration_execution["dataBoundaries"]} == {
        "preview_only_execution",
        "idempotency_without_payload",
        "provider_result_redaction",
        "operator_review_before_mutation",
    }
    assert integration_execution["api"]["standalone"] == "GET /demo/integration-execution"
    assert integration_execution["api"]["preview"] == (
        "POST /tenants/{tenant_id}/integration-executions/preview"
    )
    assert {item["path"] for item in integration_execution["docs"]} >= {
        "docs/public/INTEGRATION_EXECUTION.md",
        "docs/public/INTEGRATION_RUNTIME.md",
        "docs/public/OUTBOX_RECOVERY.md",
    }
    business_scenario_replay = payload["businessScenarioReplay"]
    assert business_scenario_replay["status"] == "validated"
    assert business_scenario_replay["command"] == "bash scripts/check_public_business_scenario_replay.sh"
    assert {item["label"] for item in business_scenario_replay["summary"]} >= {
        "Scenario groups",
        "Source systems",
        "Operator actions",
        "External writes",
    }
    scenario_replay_by_id = {item["id"]: item for item in business_scenario_replay["scenarios"]}
    assert set(scenario_replay_by_id) == {
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    }
    assert {item["stage"] for item in business_scenario_replay["flow"]} == {
        "signal",
        "normalize",
        "detect",
        "plan",
        "execute",
    }
    assert {item["path"] for item in business_scenario_replay["docs"]} >= {
        "docs/public/BUSINESS_SCENARIO_REPLAY.md",
        "docs/public/BUSINESS_CONTROL_TOWER.md",
        "docs/public/API_BACKED_DEMO.md",
        "docs/public/TECHNICAL_CAPABILITY_MAP.md",
    }
    assert len(payload["integrationJobs"]) >= 3
    assert len(payload["integrationHealth"]) >= 6
    assert any(item["name"] == "Connection diagnostics" for item in payload["integrationReadiness"])
    assert any(item["name"] == "Reconciliation evidence" for item in payload["integrationReadiness"])
    assert any(item["name"] == "Incident runbooks" for item in payload["integrationReadiness"])
    assert any(item["metric"] == "drivedesk_integration_reconciliations" for item in payload["integrationHealth"])
    assert any(item["metric"] == "drivedesk_integration_incidents" for item in payload["integrationHealth"])
    assert payload["alertRouting"]["summary"]
    assert {route["name"] for route in payload["alertRouting"]["routes"]} >= {
        "platform-critical-page",
        "platform-warning-ticket",
        "scheduled-validation-notice",
    }
    assert {binding["alert"] for binding in payload["alertRouting"]["bindings"]} >= {
        "DriveDeskApiTargetDown",
        "DriveDeskIntegrationDeadLetters",
        "DriveDeskScheduledValidationMissed",
    }
    assert {binding["state"] for binding in payload["alertRouting"]["bindings"]} == {"routed"}
    assert {action["evidence"] for action in payload["alertRouting"]["runbookActions"]} >= {
        "ALERT_ROUTING_EVIDENCE.md",
        "alert.silence.created",
    }
    assert payload["incidentResponse"]["summary"]
    assert {incident["status"] for incident in payload["incidentResponse"]["incidents"]} >= {
        "open",
        "acknowledged",
        "resolved",
    }
    assert {incident["alert"] for incident in payload["incidentResponse"]["incidents"]} >= {
        "DriveDeskApiHighLatencyP95",
        "DriveDeskIntegrationDeadLetters",
        "DriveDeskScheduledValidationMissed",
    }
    assert {event["event"] for event in payload["incidentResponse"]["timeline"]} >= {
        "alert.fired",
        "integration.incident.status_changed",
        "incident.resolved",
    }
    assert {action["evidence"] for action in payload["incidentResponse"]["recoveryActions"]} >= {
        "outbox.retry.requested",
        "postcheck.gates.passed",
        "incident.resolved",
    }
    assert {item["evidence"] for item in payload["incidentResponse"]["resolutionEvidence"]} >= {
        "drivedesk_integration_incidents",
        "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "postcheck.gates.passed",
    }
    assert len(payload["recoveryEvidence"]) >= 4
    assert payload["engineeringProof"]["milestone"] == "engineering_70"
    assert payload["engineeringProof"]["status"] == "validated"
    assert len(payload["engineeringProof"]["summary"]) >= 4
    assert len(payload["engineeringProof"]["gates"]) >= 5
    assert {gate["name"] for gate in payload["engineeringProof"]["gates"]} >= {
        "Core smoke",
        "Public demo API",
        "Backup and restore",
        "Release safety",
        "GitOps and IaC",
    }
    gate_by_name = {gate["name"]: gate for gate in payload["engineeringProof"]["gates"]}
    assert gate_by_name["Core smoke"]["command"] == "bash scripts/ci_smoke_public.sh"
    assert {item["kind"] for item in payload["engineeringProof"]["evidence"]} >= {"doc", "sdk"}
    assert any(item["path"] == "docs/public/SYSTEM_REVIEW_PATH.md" for item in payload["engineeringProof"]["evidence"])
    assert any(item["path"] == "docs/public/REVIEWER_QUICKSTART.md" for item in payload["engineeringProof"]["evidence"])
    assert any(item["path"] == "sdk/generated/public-demo/" for item in payload["engineeringProof"]["evidence"])
    assert {item["evidence"] for item in payload["recoveryEvidence"]} >= {
        "backup_sha256_recorded",
        "restore_integrity_ok",
        "counts_match",
        "production_data_touched_false",
        "release.rollback.executed",
        "stable_release_healthy_after_rollback",
        "release.canary_gate.blocked",
        "promotion_blocked",
        "burn_rate_violation_detected",
        "release.staged_promotion.completed",
        "production_approval_recorded",
        "promotion_history_hash_recorded",
        "runtime.rollout.evidence_collected",
        "loopback_boundary_recorded",
        "infra.private_state.validated",
        "no_runtime_mutation_recorded",
        "infra.remediation.plan.ready",
        "rollback_attached",
        "infra.remediation.execution.completed",
        "post_remediation_validation_recorded",
        "infra.post_remediation_drift.clean",
        "no_residual_drift_recorded",
        "infra.scheduled_validation.healthy",
        "missed_run_guard_recorded",
        "infra.scheduled_validation.alerting.ready",
        "public-scheduled-validation-alert",
    }
    assert len(payload["outbox"]) >= 3
    assert {event["status"] for event in payload["outbox"]} >= {"processed", "pending"}
    assert {job["status"] for job in payload["integrationJobs"]} >= {"processed", "retry", "dead_letter"}
    assert {item["state"] for item in payload["integrationHealth"]} >= {
        "processed",
        "retry",
        "dead_letter",
    }


def test_public_demo_can_load_api_backed_data_with_static_fallback() -> None:
    script = (DEMO_DIR / "app.js").read_text(encoding="utf-8")

    assert "loadApiBackedDemoData" in script
    assert "operationContracts" in script
    assert "operations: " in script
    assert "auth: " in script
    assert "auth boundary: " in script
    assert "real provider secret" in script
    assert "public secret" in script
    assert "Array.isArray(payload.adapters)" in script
    assert "Array.isArray(payload.adapterStudio.summary)" in script
    assert "Array.isArray(payload.connectorCertification.summary)" in script
    assert "Array.isArray(payload.connectorCertification.providerProfiles)" in script
    assert "fillConnectorCertification" in script
    assert "connectorCertificationProviderRows" in script
    assert "connectorCertificationGateRows" in script
    assert "Array.isArray(payload.connectorFixtureReplay.summary)" in script
    assert "fillConnectorFixtureReplay" in script
    assert "connectorReplayOutcomeRows" in script
    assert "connectorReplayBoundaryRows" in script
    assert "fillAdapterStudio" in script
    assert "adapterStudioPlanRows" in script
    assert "safe public execution: " in script
    assert "safeToRunAgainstPublicDemo" in script
    assert "operationPlans" in script
    assert "boundaries" in script
    assert "diagnostics" in script
    assert "fillWorkflow" in script
    assert "fillWorkflowScenarios" in script
    assert "fillEndToEndScenario" in script
    assert "fillWorkflowTimeline" in script
    assert "fillDomainEvents" in script
    assert "fillAdapterScenarios" in script
    assert "fillRecoveryEvidence" in script
    assert "fillAlertRouting" in script
    assert "fillIncidentResponse" in script
    assert "fillEngineeringProof" in script
    assert "fillBusinessContextAssistant" in script
    assert "fillBusinessActionExecution" in script
    assert "fillBusinessApprovalGateway" in script
    assert "fillIntegrationRuntime" in script
    assert "fillIntegrationExecution" in script
    assert "alertRouting" in script
    assert "incidentResponse" in script
    assert "engineeringProof" in script
    assert "businessContextAssistant" in script
    assert "businessActionExecution" in script
    assert "businessApprovalGateway" in script
    assert "integrationRuntime" in script
    assert "integrationExecution" in script
    assert "workflowScenarios" in script
    assert "endToEndScenario" in script
    assert "adapterScenarios" in script
    assert "recoveryEvidence" in script
    assert "demoApi" in script
    assert "data-demo-api-path" not in script
    assert "dataset.demoApiPath" in script
    assert "/demo/public" in script
    assert "static.fallback" not in script
    assert "api.synthetic" not in script
    assert "fetch(url" in script
    assert "return fallbackData" in script


def test_public_demo_api_scripts_and_examples_exist() -> None:
    expected = {
        "scripts/run_public_demo_local.sh",
        "scripts/check_public_demo_api.sh",
        "scripts/check_public_business_notification_channels.sh",
        "scripts/check_public_business_context_assistant.sh",
        "scripts/check_public_business_action_execution.sh",
        "scripts/check_public_business_scenario_replay.sh",
        "scripts/check_public_engineering_proof.sh",
        "scripts/check_public_demo_sdk.sh",
        "scripts/check_public_backup_restore.sh",
        "scripts/check_public_release_rollback.sh",
        "scripts/check_public_slo_canary_gate.sh",
        "scripts/check_public_staged_promotion.sh",
        "scripts/check_public_helm_render.sh",
        "scripts/check_public_opentofu_plan.sh",
        "scripts/check_public_infra_state_drift.sh",
        "scripts/check_public_runtime_rollout.sh",
        "scripts/check_public_private_infra_validation.sh",
        "scripts/check_public_private_infra_remediation.sh",
        "scripts/check_public_private_infra_remediation_execution.sh",
        "scripts/check_public_private_infra_post_remediation_drift_refresh.sh",
        "scripts/check_public_private_infra_scheduled_validation.sh",
        "scripts/check_public_gitops_layout.sh",
        "scripts/check_public_gitops_image_automation.sh",
        "scripts/check_public_gitops_promotion_drift.sh",
        "scripts/check_public_gitops_drift_remediation.sh",
        "scripts/generate_public_demo_sdk.py",
        "examples/curl/demo-public.sh",
        "examples/python/demo_public_client.py",
        "examples/python/demo_adapter_operation_plan.py",
        "examples/js/demo-public-fetch.js",
        "examples/js/demo-adapter-operation-plan.mjs",
        "sdk/generated/public-demo/README.md",
        "sdk/generated/public-demo/openapi-client-manifest.json",
        "sdk/generated/public-demo/python/drivedesk_public_demo_client.py",
        "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs",
        "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts",
    }

    for relative in expected:
        assert (ROOT / relative).is_file(), relative


def test_public_demo_api_scripts_and_examples_target_demo_contract() -> None:
    scripts = {
        "scripts/run_public_demo_local.sh": ["uvicorn", "/demo/public"],
        "scripts/check_public_demo_api.sh": [
            "/health",
            "/ready",
            "/demo/public",
            "/demo/connector-fixture-replay",
            "/demo/business-notification-channels",
            "/demo/business-context-assistant",
            "/demo/business-action-execution",
            "/demo/business-approval-gateway",
            "/demo/business-scenario-replay",
            "/openapi.json",
            "student_sync",
        ],
        "scripts/check_public_demo_sdk.sh": [
            "generate_public_demo_sdk.py",
            "sdk/generated/public-demo",
            "drivedesk_public_demo_client.py",
            "drivedesk-public-demo-client.mjs",
        ],
        "scripts/check_public_backup_restore.sh": [
            "public_synthetic_backup_restore",
            "backup_restore.drill.completed",
            "restore_integrity_ok",
            "production_data_touched",
        ],
        "scripts/check_public_release_rollback.sh": [
            "public_synthetic_release_rollback",
            "release.rollback.executed",
            "candidate_health_failure_detected",
            "stable_release_healthy_after_rollback",
        ],
        "scripts/check_public_slo_canary_gate.sh": [
            "public_synthetic_slo_canary_gate",
            "release.canary_gate.blocked",
            "promotion_blocked",
            "burn_rate_violation_detected",
        ],
        "scripts/check_public_staged_promotion.sh": [
            "public_synthetic_staged_promotion",
            "release.staged_promotion.completed",
            "production_approval_recorded",
            "promotion_history_hash_recorded",
        ],
        "scripts/check_public_helm_render.sh": [
            "public_helm_chart_render",
            "api_deployment_template_present",
            "runtime_secret_refs_present",
            "helm_template_ran",
        ],
        "scripts/check_public_opentofu_plan.sh": [
            "public_opentofu_plan",
            "state_boundary_recorded",
            "plan_only_no_apply",
            "destroy_count_zero",
        ],
        "scripts/check_public_infra_state_drift.sh": [
            "public_infra_state_drift",
            "state_backend_boundary_preserved",
            "plan_only_no_apply",
            "infra.state_drift.detected",
        ],
        "scripts/check_public_runtime_rollout.sh": [
            "public_runtime_rollout_evidence",
            "loopback_boundary_recorded",
            "runtime.rollout.evidence_collected",
            "private_staging",
        ],
        "scripts/check_public_private_infra_validation.sh": [
            "public_private_infra_validation",
            "read_only_collector_recorded",
            "no_runtime_mutation_recorded",
            "infra.private_state.validated",
        ],
        "scripts/check_public_private_infra_remediation.sh": [
            "public_private_infra_remediation_plan",
            "plan_only_no_apply",
            "rollback_attached",
            "infra.remediation.plan.ready",
        ],
        "scripts/check_public_private_infra_remediation_execution.sh": [
            "public_private_infra_remediation_execution",
            "reviewed_execution_recorded",
            "post_remediation_validation_recorded",
            "infra.remediation.execution.completed",
        ],
        "scripts/check_public_private_infra_post_remediation_drift_refresh.sh": [
            "public_private_infra_post_remediation_drift_refresh",
            "read_only_refresh_recorded",
            "no_residual_drift_recorded",
            "infra.post_remediation_drift.clean",
        ],
        "scripts/check_public_private_infra_scheduled_validation.sh": [
            "public_private_infra_scheduled_validation",
            "workflow_schedule_present",
            "missed_run_guard_recorded",
            "infra.scheduled_validation.healthy",
        ],
        "scripts/check_public_gitops_layout.sh": [
            "public_gitops_layout",
            "argocd_applications_present",
            "staged_promotion_order_present",
            "evidence_gates_referenced",
        ],
        "scripts/check_public_gitops_image_automation.sh": [
            "public_gitops_image_automation",
            "image_digest_recorded",
            "pull_request_only_no_mutation",
            "gitops.image_update.proposed",
        ],
        "scripts/check_public_gitops_promotion_drift.sh": [
            "public_gitops_promotion_drift",
            "drift_detected",
            "out_of_sync_recorded",
            "gitops-candidate-2026-06-18",
        ],
        "scripts/check_public_gitops_drift_remediation.sh": [
            "public_gitops_drift_remediation",
            "production_requires_approval",
            "plan_only_no_cluster_mutation",
            "gitops.drift_remediation.planned",
        ],
        "scripts/generate_public_demo_sdk.py": [
            "/demo/public",
            "/demo/connector-fixture-replay",
            "/demo/business-notification-channels",
            "/demo/business-context-assistant",
            "/demo/business-action-execution",
            "/demo/business-approval-gateway",
            "/demo/business-scenario-replay",
            "operationId",
            "ConnectorFixtureReplayRead",
            "BusinessNotificationChannelMatrixDemoRead",
            "BusinessContextAssistantDemoRead",
            "BusinessActionExecutionDemoRead",
            "BusinessApprovalGatewayDemoRead",
            "BusinessScenarioReplayRead",
            "drivedesk_public_demo_client.py",
            "drivedesk-public-demo-client.mjs",
        ],
        "scripts/check_public_business_action_execution.sh": [
            "/demo/business-action-execution",
            "businessActionExecution",
            "business_action_execution.previewed",
            "idempotencyKey",
            "no_provider_write",
            "BUSINESS_ACTION_EXECUTION.md",
        ],
        "scripts/check_public_business_approval_gateway.sh": [
            "/demo/business-approval-gateway",
            "businessApprovalGateway",
            "business_approval_gateway.previewed",
            "providerWriteUnlocked",
            "safe_approval_payload",
            "BUSINESS_APPROVAL_GATEWAY.md",
        ],
        "scripts/check_public_integration_runtime.sh": [
            "/demo/integration-runtime",
            "integrationRuntime",
            "adapter_runtime.previewed",
            "accounting_export_execute",
            "providerCallEnabled",
            "INTEGRATION_RUNTIME.md",
        ],
        "scripts/check_public_integration_execution.sh": [
            "/demo/integration-execution",
            "integrationExecution",
            "integration_execution.run_ledger_prepared",
            "IntegrationReconciliation",
            "INTEGRATION_EXECUTION.md",
        ],
        "examples/curl/demo-public.sh": ["/demo/public", "api.synthetic", "student_sync"],
        "examples/python/demo_public_client.py": ["/demo/public", "api.synthetic", "student_sync"],
        "examples/python/demo_adapter_operation_plan.py": [
            "get_adapter_operation_plan",
            "adapter-file-import-preview",
            "contract_only",
        ],
        "examples/js/demo-public-fetch.js": ["/demo/public", "api.synthetic", "student_sync"],
        "examples/js/demo-adapter-operation-plan.mjs": [
            "getAdapterOperationPlan",
            "adapter-file-import-preview",
            "contract_only",
        ],
        "sdk/generated/public-demo/python/drivedesk_public_demo_client.py": [
            "/demo/public",
            "/demo/connector-fixture-replay",
            "/demo/business-scenario-replay",
            "public_demo_demo_public_get",
            "connector_fixture_replay_demo_demo_connector_fixture_replay_get",
            "business_scenario_replay_demo_demo_business_scenario_replay_get",
            "student_sync",
            "get_connector_fixture_replay",
            "get_business_scenario_replay",
            "build_adapter_operation_plan",
            "contract_only",
        ],
        "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs": [
            "/demo/public",
            "/demo/connector-fixture-replay",
            "/demo/business-scenario-replay",
            "public_demo_demo_public_get",
            "connector_fixture_replay_demo_demo_connector_fixture_replay_get",
            "business_scenario_replay_demo_demo_business_scenario_replay_get",
            "student_sync",
            "getConnectorFixtureReplay",
            "getBusinessScenarioReplay",
            "buildAdapterOperationPlan",
            "contract_only",
        ],
        "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts": [
            "PublicDemoPayload",
            "ConnectorFixtureReplayPayload",
            "BusinessScenarioReplayPayload",
            "student_sync",
            "getConnectorFixtureReplay",
            "getBusinessScenarioReplay",
            "AdapterOperationPlan",
        ],
    }

    for relative, required_fragments in scripts.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for fragment in required_fragments:
            assert fragment in text, f"{fragment} missing from {relative}"


def test_public_demo_has_no_private_runtime_markers() -> None:
    private_patterns = [
        r"auto\s*school\s*54",
        r"auto" r"school54",
        r"duck" r"dns",
        r"land" r"vps",
        r"215" r"689",
        r"185" r"\.80\.",
        r"152" r"\.53\.",
        r"2a0a:",
        r"/opt/",
        r"\.env",
        r"xr" r"ay",
        r"telegram token",
        r"private key",
        r"password",
    ]
    ipv4_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    for path in DEMO_DIR.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for pattern in private_patterns:
            assert not re.search(pattern, lowered), f"{pattern} found in {path}"
        assert not ipv4_pattern.search(text), f"IPv4 address found in {path}"
