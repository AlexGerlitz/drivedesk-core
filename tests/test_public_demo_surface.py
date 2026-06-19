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
    assert 'id="controlTowerObservationRows"' in html
    assert 'id="controlTowerExceptionRows"' in html
    assert 'id="controlTowerRepairRows"' in html
    assert 'id="integrationHealthRows"' in html
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
    assert len(payload["adapterScenarios"]) >= 4
    adapter_scenario_by_id = {scenario["id"]: scenario for scenario in payload["adapterScenarios"]}
    assert set(adapter_scenario_by_id) >= {
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
        "file.import.fake",
        "accounting.export.mock",
    }
    assert {scenario["requiredScope"] for scenario in payload["adapterScenarios"]} >= {
        "file_import:preview",
        "file_import:execute",
        "accounting:export",
    }
    assert {
        output
        for scenario in payload["adapterScenarios"]
        for output in scenario["outputs"]
    } >= {
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
    assert adapter_scenario_by_id["adapter-accounting-export-retry"]["status"] == "retry"
    assert adapter_scenario_by_id["adapter-dead-letter-review"]["status"] == "dead_letter"
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
    assert "alertRouting" in script
    assert "incidentResponse" in script
    assert "engineeringProof" in script
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
        "scripts/check_public_demo_api.sh": ["/health", "/ready", "/demo/public", "/openapi.json", "student_sync"],
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
            "operationId",
            "drivedesk_public_demo_client.py",
            "drivedesk-public-demo-client.mjs",
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
            "public_demo_demo_public_get",
            "student_sync",
            "build_adapter_operation_plan",
            "contract_only",
        ],
        "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs": [
            "/demo/public",
            "public_demo_demo_public_get",
            "student_sync",
            "buildAdapterOperationPlan",
            "contract_only",
        ],
        "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts": [
            "PublicDemoPayload",
            "student_sync",
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
