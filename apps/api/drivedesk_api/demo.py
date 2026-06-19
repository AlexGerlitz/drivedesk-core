from __future__ import annotations

from typing import Any

from drivedesk_core import (
    build_adapter_execution_timeline,
    build_adapter_runtime_plan,
    build_connector_certification_workbench,
    build_provider_onboarding_workbench,
    list_adapter_descriptors,
)


def _public_operation_contracts(descriptor: dict[str, Any]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for contract in descriptor.get("operation_contracts", []):
        if not isinstance(contract, dict):
            continue
        contracts.append(
            {
                "key": contract.get("key", ""),
                "title": contract.get("title", ""),
                "trigger": contract.get("trigger", ""),
                "eventType": contract.get("event_type", ""),
                "endpoint": contract.get("endpoint", ""),
                "requiredConnectionScope": contract.get("required_connection_scope"),
                "idempotencyKeys": contract.get("idempotency_keys", []),
                "retryable": contract.get("retryable", False),
                "deadLetter": contract.get("dead_letter", False),
                "operatorReview": contract.get("operator_review", False),
            }
        )
    return contracts


def _public_auth_profile(descriptor: dict[str, Any]) -> dict[str, Any]:
    profile = descriptor.get("auth_profile", {})
    if not isinstance(profile, dict):
        profile = {}
    return {
        "mode": profile.get("mode", "unspecified"),
        "publicDemoRequiresSecret": profile.get("public_demo_requires_secret", False),
        "realProviderRequiresSecret": profile.get("real_provider_requires_secret", False),
        "secretRefs": profile.get("secret_refs", []),
        "credentialPlacement": profile.get("credential_placement", "unspecified"),
        "tokenExchange": profile.get("token_exchange", "unspecified"),
        "externalTokenExchange": profile.get("external_token_exchange", False),
        "dataBoundaries": profile.get("data_boundaries", []),
    }


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _public_camelize(value: Any) -> Any:
    if isinstance(value, list):
        return [_public_camelize(item) for item in value]
    if isinstance(value, dict):
        return {
            _snake_to_camel(str(key)): _public_camelize(item)
            for key, item in value.items()
        }
    return value


def _public_adapter_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for descriptor in list_adapter_descriptors():
        rows.append(
            {
                "key": descriptor["key"],
                "name": descriptor["name"],
                "status": descriptor["status"],
                "direction": descriptor["direction"],
                "connectionProfileSupported": descriptor["connection_profile_supported"],
                "requiredMappingKeys": descriptor["required_mapping_keys"],
                "supportedConnectionScopes": descriptor["supported_connection_scopes"],
                "defaultConnectionScopes": descriptor["default_connection_scopes"],
                "operationContracts": _public_operation_contracts(descriptor),
                "authProfile": _public_auth_profile(descriptor),
                "contract": descriptor["purpose"],
            }
        )
    return rows


def _public_integration_runtime() -> dict[str, Any]:
    runtime = build_adapter_runtime_plan(
        "accounting.export.mock",
        operation_key="accounting_export_execute",
        scopes=["accounting:export"],
        execution_mode="contract_only",
    )
    contract = runtime["operation_contract"]
    outbox_handoff = runtime["outbox_handoff"]
    worker_boundary = runtime["worker_boundary"]

    operation_contract = {
        "key": contract["key"],
        "title": contract["title"],
        "trigger": contract["trigger"],
        "eventType": contract["event_type"],
        "endpoint": contract["endpoint"],
        "requiredConnectionScope": contract["required_connection_scope"],
        "idempotencyKeys": contract["idempotency_keys"],
        "retryable": contract["retryable"],
        "deadLetter": contract["dead_letter"],
        "operatorReview": contract["operator_review"],
    }
    runtime_steps = [
        {
            "step": item["step"],
            "status": item["status"],
            "detail": item["detail"],
            "evidence": item["evidence"],
        }
        for item in runtime["runtime_steps"]
    ]
    preflight_checks = [
        {
            "check": item["check"],
            "status": item["status"],
            "detail": item["detail"],
            "externalMutation": item["external_mutation"],
            "providerCallEnabled": item.get("provider_call_enabled", False),
            "secretRefsVisible": item.get("secret_refs_visible", False),
            "evidence": item["evidence"],
        }
        for item in runtime["preflight_checks"]
    ]
    reconciliation_plan = [
        {
            "step": item["step"],
            "status": item["status"],
            "detail": item["detail"],
            "externalMutation": item["external_mutation"],
            "evidence": item["evidence"],
        }
        for item in runtime["reconciliation_plan"]
    ]
    incident_routes = [
        {
            "route": item["route"],
            "status": item["status"],
            "source": item["source"],
            "runbook": item["runbook"],
            "externalMutation": item["external_mutation"],
            "evidence": item["evidence"],
        }
        for item in runtime["incident_routes"]
    ]
    data_boundaries = [
        {
            "name": item["name"],
            "status": item["status"],
            "externalMutation": item.get("external_mutation", False),
            "containsPii": item.get("contains_pii", False),
            "rawPayloadIncluded": item.get("raw_payload_included", False),
            "secretRefs": item.get("secret_refs", []),
            "detail": item["detail"],
        }
        for item in runtime["data_boundaries"]
    ]

    return {
        "status": "previewed",
        "command": "POST /tenants/{tenant_id}/integration-runtime/preview",
        "summary": [
            {
                "label": "Runtime steps",
                "value": str(len(runtime_steps)),
                "detail": "contract to reconciliation",
                "tone": "blue",
            },
            {
                "label": "Adapter",
                "value": "accounting",
                "detail": "accounting.export.mock",
                "tone": "green",
            },
            {
                "label": "Outbox",
                "value": outbox_handoff["status"],
                "detail": outbox_handoff["would_enqueue_event"],
                "tone": "violet",
            },
            {
                "label": "Provider calls",
                "value": "0",
                "detail": "contract-only public preview",
                "tone": "amber",
            },
        ],
        "adapterKey": runtime["adapter_key"],
        "operationKey": operation_contract["key"],
        "executionMode": "contract_only",
        "operationContract": operation_contract,
        "runtimeSteps": runtime_steps,
        "preflightChecks": preflight_checks,
        "outboxHandoff": {
            "status": outbox_handoff["status"],
            "wouldEnqueueEvent": outbox_handoff["would_enqueue_event"],
            "adapterKey": outbox_handoff["adapter_key"],
            "operationKey": outbox_handoff["operation_key"],
            "requiredConnectionScope": outbox_handoff["required_connection_scope"],
            "idempotencyKeys": outbox_handoff["idempotency_keys"],
            "retryable": outbox_handoff["retryable"],
            "deadLetter": outbox_handoff["dead_letter"],
            "operatorReview": outbox_handoff["operator_review"],
            "externalMutation": outbox_handoff["external_mutation"],
            "providerCallEnabled": outbox_handoff["provider_call_enabled"],
            "evidence": outbox_handoff["evidence"],
        },
        "workerBoundary": {
            "status": worker_boundary["status"],
            "endpoint": worker_boundary["endpoint"],
            "workerFunction": worker_boundary["worker_function"],
            "executionMode": worker_boundary["execution_mode"],
            "publicRunMode": worker_boundary["public_run_mode"],
            "externalMutation": worker_boundary["external_mutation"],
            "providerCallEnabled": worker_boundary["provider_call_enabled"],
            "rawPayloadIncluded": worker_boundary["raw_payload_included"],
            "containsPii": worker_boundary["contains_pii"],
            "evidence": worker_boundary["evidence"],
        },
        "reconciliationPlan": reconciliation_plan,
        "incidentRoutes": incident_routes,
        "dataBoundaries": data_boundaries,
        "api": {
            "standalone": "GET /demo/integration-runtime",
            "preview": "POST /tenants/{tenant_id}/integration-runtime/preview",
            "adapters": "GET /integration-adapters",
            "runbooks": "GET /integration-runbooks",
            "operatorReview": "GET /tenants/{tenant_id}/integration-operator-review",
        },
        "docs": [
            {
                "label": "Integration runtime",
                "path": "docs/public/INTEGRATION_RUNTIME.md",
                "check": "bash scripts/check_public_integration_runtime.sh",
            },
            {
                "label": "Operation contracts",
                "path": "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
                "check": "bash scripts/check_public_demo_api.sh",
            },
            {
                "label": "Adapter developer guide",
                "path": "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
                "check": "bash scripts/check_public_adapter_developer_guide.sh",
            },
        ],
    }


def _public_integration_execution() -> dict[str, Any]:
    execution = build_adapter_execution_timeline(
        "accounting.export.mock",
        operation_key="accounting_export_execute",
        scopes=["accounting:export"],
        execution_mode="contract_only",
        request_id="public-demo-accounting-export-001",
        include_failure_path=True,
    )
    run_ledger = execution["run_ledger"]
    timeline = [
        {
            "stage": item["stage"],
            "status": item["status"],
            "detail": item["detail"],
            "wouldRecord": item.get("would_record"),
            "externalMutation": item["external_mutation"],
            "providerCallEnabled": item.get("provider_call_enabled", False),
            "evidence": item["evidence"],
        }
        for item in execution["timeline"]
    ]
    state_transitions = [
        {
            "from": item["from"],
            "to": item["to"],
            "trigger": item["trigger"],
            "evidence": item["evidence"],
        }
        for item in execution["state_transitions"]
    ]
    retry_policy = [
        {
            "name": item["name"],
            "status": item["status"],
            "trigger": item["trigger"],
            "maxAttempts": item["max_attempts"],
            "externalMutation": item["external_mutation"],
            "evidence": item["evidence"],
        }
        for item in execution["retry_policy"]
    ]
    reconciliation_links = [
        {
            "name": item["name"],
            "status": item["status"],
            "source": item["source"],
            "wouldRecord": item["would_record"],
            "evidence": item["evidence"],
        }
        for item in execution["reconciliation_links"]
    ]
    observability = [
        {
            "metric": item["metric"],
            "status": item["status"],
            "labels": item["labels"],
            "evidence": item["evidence"],
        }
        for item in execution["observability"]
    ]
    data_boundaries = [
        {
            "name": item["name"],
            "status": item["status"],
            "externalMutation": item.get("external_mutation", False),
            "containsPii": item.get("contains_pii", False),
            "rawPayloadIncluded": item.get("raw_payload_included", False),
            "idempotencyKeys": item.get("idempotency_keys", []),
            "detail": item["detail"],
        }
        for item in execution["data_boundaries"]
    ]

    return {
        "status": "previewed",
        "command": "POST /tenants/{tenant_id}/integration-executions/preview",
        "summary": [
            {
                "label": "Timeline",
                "value": str(len(timeline)),
                "detail": "request to closure",
                "tone": "blue",
            },
            {
                "label": "Run ledger",
                "value": "planned",
                "detail": str(run_ledger["run_id"]),
                "tone": "green",
            },
            {
                "label": "Provider calls",
                "value": "0",
                "detail": "blocked in public preview",
                "tone": "amber",
            },
            {
                "label": "Recovery",
                "value": "armed",
                "detail": "retry, dead-letter, reconciliation",
                "tone": "violet",
            },
        ],
        "adapterKey": execution["adapter_key"],
        "operationKey": execution["operation_key"],
        "executionMode": execution["execution_mode"],
        "runLedger": {
            "runId": run_ledger["run_id"],
            "requestId": run_ledger["request_id"],
            "adapterKey": run_ledger["adapter_key"],
            "operationKey": run_ledger["operation_key"],
            "eventType": run_ledger["event_type"],
            "status": run_ledger["status"],
            "executionMode": run_ledger["execution_mode"],
            "idempotencyFingerprint": run_ledger["idempotency_fingerprint"],
            "wouldCreateWorkflowActionRun": run_ledger["would_create_workflow_action_run"],
            "wouldCreateOutboxEvent": run_ledger["would_create_outbox_event"],
            "wouldCallProvider": run_ledger["would_call_provider"],
            "externalMutation": run_ledger["external_mutation"],
            "rawPayloadIncluded": run_ledger["raw_payload_included"],
            "containsPii": run_ledger["contains_pii"],
            "evidence": run_ledger["evidence"],
        },
        "timeline": timeline,
        "stateTransitions": state_transitions,
        "retryPolicy": retry_policy,
        "reconciliationLinks": reconciliation_links,
        "observability": observability,
        "dataBoundaries": data_boundaries,
        "api": {
            "standalone": "GET /demo/integration-execution",
            "preview": "POST /tenants/{tenant_id}/integration-executions/preview",
            "runtimePreview": "POST /tenants/{tenant_id}/integration-runtime/preview",
            "workflowActionRuns": "GET /tenants/{tenant_id}/workflow-action-runs",
            "outbox": "GET /tenants/{tenant_id}/outbox-events",
            "reconciliations": "GET /tenants/{tenant_id}/integration-reconciliations",
            "incidents": "GET /tenants/{tenant_id}/integration-incidents",
        },
        "docs": [
            {
                "label": "Integration execution",
                "path": "docs/public/INTEGRATION_EXECUTION.md",
                "check": "bash scripts/check_public_integration_execution.sh",
            },
            {
                "label": "Integration runtime",
                "path": "docs/public/INTEGRATION_RUNTIME.md",
                "check": "bash scripts/check_public_integration_runtime.sh",
            },
            {
                "label": "Outbox recovery",
                "path": "docs/public/OUTBOX_RECOVERY.md",
                "check": "bash scripts/check_public_demo_api.sh",
            },
        ],
    }


def _public_connector_certification() -> dict[str, Any]:
    workbench = build_connector_certification_workbench()
    provider_profiles = [
        {
            "adapterKey": item["adapter_key"],
            "name": item["name"],
            "category": item["category"],
            "direction": item["direction"],
            "status": item["status"],
            "operationCount": item["operation_count"],
            "capabilityCount": item["capability_count"],
            "connectionProfileSupported": item["connection_profile_supported"],
            "serverSecretBoundary": item["server_secret_boundary"],
            "requiresRealProviderSecret": item["requires_real_provider_secret"],
            "publicDemoRequiresSecret": item["public_demo_requires_secret"],
            "scopeBoundary": item["scope_boundary"],
            "idempotencyBoundary": item["idempotency_boundary"],
            "recoveryBoundary": item["recovery_boundary"],
            "publicSafe": item["public_safe"],
            "readyForPrivateConnector": item["ready_for_private_connector"],
            "evidence": item["evidence"],
        }
        for item in workbench["provider_profiles"]
    ]
    certification_gates = [
        {
            "gate": item["gate"],
            "status": item["status"],
            "detail": item["detail"],
            "externalMutation": item["external_mutation"],
            "evidence": item["evidence"],
        }
        for item in workbench["certification_gates"]
    ]
    implementation_path = [
        {
            "step": item["step"],
            "status": item["status"],
            "detail": item["detail"],
            "evidence": item["evidence"],
        }
        for item in workbench["implementation_path"]
    ]
    data_boundaries = [
        {
            "name": item["name"],
            "status": item["status"],
            "containsPii": item["contains_pii"],
            "rawPayloadIncluded": item["raw_payload_included"],
            "externalMutation": item["external_mutation"],
            "detail": item["detail"],
        }
        for item in workbench["data_boundaries"]
    ]
    return {
        "status": workbench["status"],
        "command": "GET /demo/connector-certification",
        "certificationLevel": workbench["certification_level"],
        "adapterCount": workbench["adapter_count"],
        "privateReadyCount": workbench["private_ready_count"],
        "summary": workbench["summary"],
        "providerProfiles": provider_profiles,
        "certificationStages": workbench["certification_stages"],
        "certificationGates": certification_gates,
        "implementationPath": implementation_path,
        "dataBoundaries": data_boundaries,
        "api": workbench["api"],
        "docs": workbench["docs"],
    }


def _public_provider_onboarding() -> dict[str, Any]:
    workbench = _public_camelize(build_provider_onboarding_workbench())
    workbench["command"] = "GET /demo/provider-onboarding"
    return workbench


def build_public_demo_payload() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "generatedAt": "2026-06-17T10:55:00Z",
        "dataSource": "api.synthetic",
        "apiContract": {
            "path": "/demo/public",
            "mode": "read_only",
            "data_profile": "synthetic_demo_data",
            "fallback": "apps/admin/public-demo/demo-data.js",
        },
        "tenant": {
            "name": "DriveDesk Demo Academy",
            "slug": "demo-academy",
            "status": "active",
            "plan": "Core Preview",
        },
        "health": {
            "api": "ready",
            "worker": "processing",
            "database": "online",
            "observability": "validated",
        },
        "metrics": [
            {
                "label": "API checks",
                "value": "48",
                "detail": "private smoke tests",
                "tone": "blue",
            },
            {
                "label": "Public CI",
                "value": "green",
                "detail": "GitHub Actions",
                "tone": "green",
            },
                {
                    "label": "OpenAPI paths",
                    "value": "48",
                    "detail": "generated contract",
                    "tone": "violet",
                },
            {
                "label": "Workflow stages",
                "value": "5",
                "detail": "lead to sync",
                "tone": "green",
            },
            {
                "label": "Pending events",
                "value": "1",
                "detail": "retry queue",
                "tone": "amber",
            },
        ],
        "workQueue": [
            {
                "id": "DD-TASK-101",
                "title": "Review new learner intake",
                "owner": "Front desk",
                "status": "in review",
                "priority": "high",
            },
            {
                "id": "DD-TASK-102",
                "title": "Prepare instructor schedule sync",
                "owner": "Ops manager",
                "status": "planned",
                "priority": "medium",
            },
            {
                "id": "DD-TASK-103",
                "title": "Check payment adapter sandbox",
                "owner": "Finance",
                "status": "blocked",
                "priority": "medium",
            },
            {
                "id": "DD-TASK-104",
                "title": "Publish demo evidence package",
                "owner": "Platform",
                "status": "done",
                "priority": "low",
            },
        ],
        "members": [
            {
                "name": "Demo Owner",
                "email": "owner@example.test",
                "role": "owner",
                "status": "active",
            },
            {
                "name": "Ops Manager",
                "email": "ops@example.test",
                "role": "manager",
                "status": "active",
            },
            {
                "name": "Instructor Lead",
                "email": "instructor@example.test",
                "role": "viewer",
                "status": "active",
            },
        ],
        "auditEvents": [
            {
                "time": "08:12",
                "actor": "seed",
                "event": "tenant.created",
                "summary": "Demo tenant initialized",
            },
            {
                "time": "08:13",
                "actor": "owner",
                "event": "membership.created",
                "summary": "Ops manager role assigned",
            },
            {
                "time": "08:14",
                "actor": "worker",
                "event": "outbox.processed",
                "summary": "Public evidence event processed",
            },
            {
                "time": "09:21",
                "actor": "workflow",
                "event": "contract.generated",
                "summary": "Demo learner contract prepared",
            },
            {
                "time": "09:22",
                "actor": "outbox",
                "event": "student.sync.requested",
                "summary": "Student sync event queued",
            },
        ],
        "outbox": [
            {
                "event": "tenant.created",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "membership.created",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "integration.file_import.requested",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "integration.provider.sync",
                "status": "pending",
                "attempts": 0,
            },
            {
                "event": "student.sync.requested",
                "status": "pending",
                "attempts": 0,
            },
        ],
        "adapters": _public_adapter_rows(),
        "adapterScenarios": [
            {
                "id": "adapter-file-import-preview",
                "title": "File import mapping preview",
                "adapter": "file.import.fake",
                "operation": "file_import_preview",
                "phase": "preview",
                "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
                "requiredScope": "file_import:preview",
                "status": "processed",
                "detail": "Tenant mapping is validated against sample records before any outbox event is created.",
                "inputs": ["connection_profile", "mapping", "records"],
                "outputs": ["mapping_preview", "validation_errors", "no_outbox_event"],
                "evidence": "integration.mapping_preview.completed",
            },
            {
                "id": "adapter-file-import-execute",
                "title": "File import execution",
                "adapter": "file.import.fake",
                "operation": "file_import_execute",
                "phase": "execute",
                "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
                "requiredScope": "file_import:execute",
                "status": "processed",
                "detail": "Accepted records are queued through the outbox with idempotency keys and an audit event.",
                "inputs": ["source_name", "source_format", "records_hash"],
                "outputs": ["outbox_event", "adapter_job", "audit_event"],
                "evidence": "integration.file_import.requested",
            },
            {
                "id": "adapter-crm-deal-preview",
                "title": "CRM deal intake preview",
                "adapter": "crm.bitrix24.mock",
                "operation": "crm_deal_intake_preview",
                "phase": "preview",
                "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                "requiredScope": "crm:deal.preview",
                "status": "mapped",
                "detail": (
                    "Bitrix-style CRM deal data is mapped into a safe provider intake preview "
                    "before DriveDesk records any business state."
                ),
                "inputs": ["provider_key", "subject_ref", "payload_hash"],
                "outputs": ["safe_payload", "normalized_observation", "no_provider_call"],
                "evidence": "business_provider_intake.previewed",
            },
            {
                "id": "adapter-crm-deal-ingest",
                "title": "CRM deal intake queue",
                "adapter": "crm.bitrix24.mock",
                "operation": "crm_deal_ingest_execute",
                "phase": "execute",
                "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
                "requiredScope": "crm:deal.ingest",
                "status": "pending",
                "detail": "Accepted CRM facts are queued through the outbox for retryable worker execution.",
                "inputs": ["batch_id", "deals_hash", "idempotency_key"],
                "outputs": ["outbox_event", "adapter_job", "redaction_evidence"],
                "evidence": "integration.crm_deal.ingest.requested",
            },
            {
                "id": "adapter-accounting-export-retry",
                "title": "Accounting export retry",
                "adapter": "accounting.export.mock",
                "operation": "accounting_export_execute",
                "phase": "retry",
                "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
                "requiredScope": "accounting:export",
                "status": "retry",
                "detail": "Temporary provider failure keeps the job retryable and visible to operations.",
                "inputs": ["export_batch_id", "documents_hash", "idempotency_key"],
                "outputs": ["retry_scheduled", "attempt_count", "operator_visible_status"],
                "evidence": "integration.export.retry_scheduled",
            },
            {
                "id": "adapter-dead-letter-review",
                "title": "Dead-letter operator review",
                "adapter": "file.import.fake",
                "operation": "file_import_execute",
                "phase": "operator_review",
                "endpoint": "GET /tenants/{tenant_id}/integration-operator-review",
                "requiredScope": "file_import:execute",
                "status": "dead_letter",
                "detail": "Permanent contract failure creates a review card with runbook context and a manual retry endpoint.",
                "inputs": ["outbox_event", "last_error", "payload_summary"],
                "outputs": ["review_card", "runbook", "manual_retry_endpoint"],
                "evidence": "integration.operator_review.created",
            },
        ],
        "adapterStudio": {
            "summary": [
                {
                    "label": "SDK plans",
                    "value": "6",
                    "detail": "Contract-only adapter operations",
                    "tone": "blue",
                },
                {
                    "label": "CRM preview",
                    "value": "safe",
                    "detail": "Redacted Bitrix-style provider intake",
                    "tone": "green",
                },
                {
                    "label": "Worker ingest",
                    "value": "outbox",
                    "detail": "Server-side retry boundary",
                    "tone": "violet",
                },
                {
                    "label": "Secrets",
                    "value": "server",
                    "detail": "No browser token storage",
                    "tone": "amber",
                },
            ],
            "flow": [
                {
                    "step": "1",
                    "name": "Runtime catalog",
                    "state": "ready",
                    "detail": (
                        "GET /integration-adapters exposes crm.bitrix24.mock descriptors, auth_profile, "
                        "scopes, and operation contracts."
                    ),
                    "evidence": "GET /integration-adapters",
                },
                {
                    "step": "2",
                    "name": "SDK operation plan",
                    "state": "contract_only",
                    "detail": (
                        "Generated Python and JavaScript SDK builds adapter-crm-deal-preview and "
                        "adapter-crm-deal-ingest request plans without live provider writes."
                    ),
                    "evidence": "sdk/generated/public-demo/",
                },
                {
                    "step": "3",
                    "name": "Preview boundary",
                    "state": "preview_only",
                    "detail": (
                        "CRM payload is normalized through business-provider-intake preview; raw payload, "
                        "phone, full_name, and access_token are dropped."
                    ),
                    "evidence": "business_provider_intake.previewed",
                },
                {
                    "step": "4",
                    "name": "Worker ingest",
                    "state": "queued",
                    "detail": (
                        "Accepted CRM facts become integration.crm_deal.ingest.requested and are handled by "
                        "worker:drivedesk_worker.main.process_pending_outbox."
                    ),
                    "evidence": "integration.crm_deal.ingest.requested",
                },
                {
                    "step": "5",
                    "name": "Diagnostics and review",
                    "state": "observable",
                    "detail": (
                        "Connection checks, reconciliations, incident cards, retry, dead-letter, and "
                        "operator_review make failures recoverable."
                    ),
                    "evidence": "drivedesk_integration_incidents",
                },
            ],
            "operationPlans": [
                {
                    "scenarioId": "adapter-crm-deal-preview",
                    "adapter": "crm.bitrix24.mock",
                    "operation": "crm_deal_intake_preview",
                    "method": "POST",
                    "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                    "scope": "crm:deal.preview",
                    "executionMode": "contract_only",
                    "safeToRunAgainstPublicDemo": False,
                    "requestShape": [
                        "dryRun",
                        "provider_key",
                        "source_type",
                        "subject_type",
                        "subject_id",
                        "external_ref",
                        "provider_payload",
                    ],
                    "safeOutputs": ["safe_payload", "normalized_observation", "no_provider_call"],
                    "evidence": "business_provider_intake.previewed",
                },
                {
                    "scenarioId": "adapter-crm-deal-ingest",
                    "adapter": "crm.bitrix24.mock",
                    "operation": "crm_deal_ingest_execute",
                    "method": "WORKER",
                    "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
                    "scope": "crm:deal.ingest",
                    "executionMode": "contract_only",
                    "safeToRunAgainstPublicDemo": False,
                    "requestShape": ["batch_id", "deals_hash", "mapping", "idempotency_key"],
                    "safeOutputs": ["outbox_event", "adapter_job", "redaction_evidence"],
                    "evidence": "integration.crm_deal.ingest.requested",
                },
            ],
            "boundaries": [
                {
                    "name": "auth_profile",
                    "state": "server_only",
                    "detail": "oauth2_or_webhook_boundary keeps token exchange in private connector code.",
                    "evidence": "server_secret_store",
                },
                {
                    "name": "browser token boundary",
                    "state": "clean",
                    "detail": (
                        "no_browser_token_storage and server_side_provider_calls_only prevent provider tokens "
                        "from entering the public UI."
                    ),
                    "evidence": "private_connector_only",
                },
                {
                    "name": "redaction",
                    "state": "clean",
                    "detail": (
                        "safe_payload excludes access_token, full_name, phone, raw provider payload, "
                        "and tenant secrets."
                    ),
                    "evidence": "redaction_evidence",
                },
                {
                    "name": "public run mode",
                    "state": "contract_only",
                    "detail": "Public demo never calls Bitrix, bank, accounting, Telegram, email, or provider APIs.",
                    "evidence": "safeToRunAgainstPublicDemo=false",
                },
            ],
            "diagnostics": [
                {
                    "name": "Connection checks",
                    "state": "passed",
                    "metric": "drivedesk_integration_connection_checks",
                    "detail": "Provider readiness without raw payloads",
                },
                {
                    "name": "Reconciliation",
                    "state": "matched",
                    "metric": "drivedesk_integration_reconciliations",
                    "detail": "Provider evidence comparison",
                },
                {
                    "name": "Incident cards",
                    "state": "open",
                    "metric": "drivedesk_integration_incidents",
                    "detail": "Runbook-backed operator flow",
                },
                {
                    "name": "Dead-letter review",
                    "state": "ready",
                    "metric": "integration.operator_review.created",
                    "detail": "Manual review for failed jobs",
                },
            ],
            "docs": [
                {
                    "label": "Adapter developer guide",
                    "path": "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
                    "check": "bash scripts/check_public_adapter_developer_guide.sh",
                },
                {
                    "label": "Generated SDK",
                    "path": "docs/public/CLIENT_SDK.md",
                    "check": "bash scripts/check_public_demo_sdk.sh",
                },
                {
                    "label": "Provider connector guide",
                    "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
                    "check": "bash scripts/check_public_provider_connector_guide.sh",
                },
            ],
        },
        "connectorCertification": _public_connector_certification(),
        "providerOnboarding": _public_provider_onboarding(),
        "integrationRuntime": _public_integration_runtime(),
        "integrationExecution": _public_integration_execution(),
        "connectorFixtureReplay": {
            "status": "validated",
            "command": "bash scripts/check_public_connector_fixture_replay.sh",
            "fixtureFile": "examples/connector-fixtures/replay-fixtures.sanitized.json",
            "evidenceFile": "docs/public/evidence/connector-fixture-replay.sanitized.json",
            "summary": [
                {
                    "label": "Fixture groups",
                    "value": "6",
                    "detail": "happy path, redaction, invalid, retry, dead-letter, reconciliation",
                    "tone": "blue",
                },
                {
                    "label": "Provider calls",
                    "value": "0",
                    "detail": "Replay is contract-only and public-safe",
                    "tone": "green",
                },
                {
                    "label": "Secrets",
                    "value": "redacted",
                    "detail": "credentials and raw payloads never return to the demo",
                    "tone": "green",
                },
                {
                    "label": "Operator path",
                    "value": "review",
                    "detail": "dead-letter and mismatch cases route to operator review",
                    "tone": "amber",
                },
            ],
            "outcomes": [
                {
                    "group": "happy_path_preview",
                    "stage": "preview",
                    "status": "passed",
                    "detail": "Normalizes external_reference, amount_bucket, status, and provider labels.",
                    "evidence": "safe_payload_present=true",
                },
                {
                    "group": "sensitive_payload_redaction",
                    "stage": "redaction",
                    "status": "passed",
                    "detail": "Drops access_token, refresh_token, full_name, phone, email, address, and raw body.",
                    "evidence": "redaction_evidence_present=true",
                },
                {
                    "group": "invalid_payload",
                    "stage": "validation",
                    "status": "blocked",
                    "detail": "Rejects malformed input without creating outbox work.",
                    "evidence": "outbox_event_created=false",
                },
                {
                    "group": "retryable_provider_failure",
                    "stage": "retry",
                    "status": "retry_scheduled",
                    "detail": "Classifies temporary provider failure as retryable.",
                    "evidence": "next_state=retry_scheduled",
                },
                {
                    "group": "dead_letter_provider_failure",
                    "stage": "operator_review",
                    "status": "dead_letter",
                    "detail": "Routes permanent provider failure into incident-backed operator review.",
                    "evidence": "integration.operator_review.created",
                },
                {
                    "group": "reconciliation_mismatch",
                    "stage": "reconciliation",
                    "status": "mismatch",
                    "detail": "Records provider evidence mismatch for manual review.",
                    "evidence": "drivedesk_integration_reconciliations",
                },
            ],
            "boundaries": [
                {
                    "name": "raw payload",
                    "state": "not_returned",
                    "detail": "raw_payload_returned=false for every fixture group",
                    "evidence": "docs/public/evidence/connector-fixture-replay.sanitized.json",
                },
                {
                    "name": "credentials",
                    "state": "not_returned",
                    "detail": "credentials_returned=false and provider tokens are excluded",
                    "evidence": "examples/connector-fixtures/replay-fixtures.sanitized.json",
                },
                {
                    "name": "external calls",
                    "state": "disabled",
                    "detail": "external_call_made=false keeps public replay offline",
                    "evidence": "CONNECTOR_FIXTURE_REPLAY.md",
                },
                {
                    "name": "persistence",
                    "state": "disabled",
                    "detail": "public_demo_persistence=false keeps replay read-only",
                    "evidence": "bash scripts/check_public_connector_fixture_replay.sh",
                },
            ],
            "docs": [
                {
                    "label": "Replay path",
                    "path": "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
                    "check": "bash scripts/check_public_connector_fixture_replay.sh",
                },
                {
                    "label": "Sanitized evidence",
                    "path": "docs/public/evidence/connector-fixture-replay.sanitized.json",
                    "check": "public-evidence-index entry",
                },
                {
                    "label": "Replay fixtures",
                    "path": "examples/connector-fixtures/replay-fixtures.sanitized.json",
                    "check": "fixture_set_id=drivedesk-core-connector-fixture-replay-fixtures",
                },
            ],
        },
        "integrationJobs": [
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "processed",
                "attempts": 1,
                "summary": "2 accepted, 1 rejected",
            },
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "retry",
                "attempts": 1,
                "summary": "temporary provider failure, next retry scheduled",
            },
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "dead_letter",
                "attempts": 1,
                "summary": "permanent contract failure, operator review required",
            },
        ],
        "integrationHealth": [
            {
                "label": "Processed jobs",
                "value": "1",
                "state": "processed",
                "detail": "file.import.fake",
                "metric": "drivedesk_integration_jobs",
            },
            {
                "label": "Retry queue",
                "value": "1",
                "state": "retry",
                "detail": "temporary provider failure",
                "metric": "drivedesk_integration_job_errors",
            },
            {
                "label": "Dead letters",
                "value": "1",
                "state": "dead_letter",
                "detail": "operator review required",
                "metric": "drivedesk_integration_jobs",
            },
            {
                "label": "Avg duration",
                "value": "12 ms",
                "state": "observed",
                "detail": "last adapter sample",
                "metric": "drivedesk_integration_adapter_duration_milliseconds",
            },
            {
                "label": "Reconciliation",
                "value": "1 match",
                "state": "matched",
                "detail": "provider evidence verified",
                "metric": "drivedesk_integration_reconciliations",
            },
            {
                "label": "Open incidents",
                "value": "2",
                "state": "open",
                "detail": "runbook-backed operator cards",
                "metric": "drivedesk_integration_incidents",
            },
        ],
        "integrationReadiness": [
            {
                "name": "File import adapter",
                "state": "active",
                "progress": 75,
            },
            {
                "name": "Payment sandbox adapter",
                "state": "waiting",
                "progress": 20,
            },
            {
                "name": "Accounting export adapter",
                "state": "active",
                "progress": 55,
            },
            {
                "name": "Connection diagnostics",
                "state": "active",
                "progress": 45,
            },
            {
                "name": "Reconciliation evidence",
                "state": "active",
                "progress": 40,
            },
            {
                "name": "Incident runbooks",
                "state": "active",
                "progress": 35,
            },
            {
                "name": "Public demo runtime",
                "state": "active",
                "progress": 35,
            },
            {
                "name": "Alert routing",
                "state": "active",
                "progress": 45,
            },
        ],
        "alertRouting": {
            "summary": [
                {
                    "label": "Routes",
                    "value": "3",
                    "detail": "critical, warning, scheduled validation",
                    "tone": "blue",
                },
                {
                    "label": "Receivers",
                    "value": "3",
                    "detail": "page, chat, ticket queue",
                    "tone": "green",
                },
                {
                    "label": "Bound alerts",
                    "value": "5",
                    "detail": "runbook-backed signals",
                    "tone": "violet",
                },
                {
                    "label": "Escalation",
                    "value": "15m",
                    "detail": "critical route to ticket queue",
                    "tone": "amber",
                },
            ],
            "routes": [
                {
                    "name": "platform-critical-page",
                    "match": "severity=critical",
                    "receiver": "public-oncall-page",
                    "repeat": "30m",
                    "escalation": "15m",
                    "artifact": "public-alert-routing-artifact",
                    "state": "active",
                },
                {
                    "name": "platform-warning-ticket",
                    "match": "severity=warning",
                    "receiver": "public-ticket-queue",
                    "repeat": "240m",
                    "escalation": "60m",
                    "artifact": "public-alert-routing-artifact",
                    "state": "active",
                },
                {
                    "name": "scheduled-validation-notice",
                    "match": "service=scheduled-validation",
                    "receiver": "public-chat-notice",
                    "repeat": "180m",
                    "escalation": "45m",
                    "artifact": "public-scheduled-validation-alert",
                    "state": "active",
                },
            ],
            "bindings": [
                {
                    "alert": "DriveDeskApiTargetDown",
                    "severity": "critical",
                    "service": "api",
                    "route": "platform-critical-page",
                    "owner": "platform",
                    "runbook": "RUNTIME_ROLLOUT_EVIDENCE.md",
                    "dedupe": "alertname:service:stage",
                    "state": "routed",
                },
                {
                    "alert": "DriveDeskApiHighLatencyP95",
                    "severity": "warning",
                    "service": "api",
                    "route": "platform-warning-ticket",
                    "owner": "platform",
                    "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
                    "dedupe": "alertname:service:stage",
                    "state": "routed",
                },
                {
                    "alert": "DriveDeskIntegrationDeadLetters",
                    "severity": "warning",
                    "service": "integrations",
                    "route": "platform-warning-ticket",
                    "owner": "integrations",
                    "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
                    "dedupe": "alertname:service:stage",
                    "state": "routed",
                },
                {
                    "alert": "DriveDeskAuthFailureSpike",
                    "severity": "critical",
                    "service": "auth",
                    "route": "platform-critical-page",
                    "owner": "security",
                    "runbook": "AUTH_OBSERVABILITY.md",
                    "dedupe": "alertname:service:stage",
                    "state": "routed",
                },
                {
                    "alert": "DriveDeskScheduledValidationMissed",
                    "severity": "warning",
                    "service": "scheduled-validation",
                    "route": "scheduled-validation-notice",
                    "owner": "platform",
                    "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
                    "dedupe": "alertname:service",
                    "state": "routed",
                },
            ],
            "runbookActions": [
                {
                    "name": "First response",
                    "detail": "Open the public runbook and inspect the sanitized evidence artifact.",
                    "state": "ready",
                    "evidence": "ALERT_ROUTING_EVIDENCE.md",
                },
                {
                    "name": "Escalation path",
                    "detail": "Critical alerts escalate to the ticket queue after 15 minutes.",
                    "state": "ready",
                    "evidence": "public-ticket-queue",
                },
                {
                    "name": "Silence contract",
                    "detail": "Maintenance silences require alertname, service, stage, and an expiry.",
                    "state": "ready",
                    "evidence": "alert.silence.created",
                },
            ],
        },
        "incidentResponse": {
            "summary": [
                {
                    "label": "Open incidents",
                    "value": "2",
                    "detail": "runbook-backed operator queue",
                    "tone": "amber",
                },
                {
                    "label": "Resolved",
                    "value": "1",
                    "detail": "mitigation evidence recorded",
                    "tone": "green",
                },
                {
                    "label": "MTTA",
                    "value": "4m",
                    "detail": "synthetic acknowledgement target",
                    "tone": "blue",
                },
                {
                    "label": "Evidence",
                    "value": "5",
                    "detail": "audit, metric, runbook, rollback, postcheck",
                    "tone": "violet",
                },
            ],
            "incidents": [
                {
                    "id": "INC-2026-06-18-001",
                    "title": "Integration dead letters require review",
                    "status": "acknowledged",
                    "severity": "warning",
                    "owner": "integrations",
                    "alert": "DriveDeskIntegrationDeadLetters",
                    "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
                    "source": "outbox.dead_letter",
                    "mitigation": "retry blocked until mapping review",
                    "evidence": "integration.incident.created",
                },
                {
                    "id": "INC-2026-06-18-002",
                    "title": "API latency warning during canary",
                    "status": "open",
                    "severity": "warning",
                    "owner": "platform",
                    "alert": "DriveDeskApiHighLatencyP95",
                    "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
                    "source": "slo.canary_gate",
                    "mitigation": "promotion remains blocked",
                    "evidence": "release.canary_gate.blocked",
                },
                {
                    "id": "INC-2026-06-18-003",
                    "title": "Scheduled validation miss recovered",
                    "status": "resolved",
                    "severity": "warning",
                    "owner": "platform",
                    "alert": "DriveDeskScheduledValidationMissed",
                    "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
                    "source": "scheduled.validation",
                    "mitigation": "manual dispatch completed",
                    "evidence": "integration.incident.status_changed",
                },
            ],
            "timeline": [
                {
                    "time": "10:00",
                    "actor": "alertmanager",
                    "state": "fired",
                    "event": "alert.fired",
                    "detail": "DriveDeskIntegrationDeadLetters routed to platform-warning-ticket",
                },
                {
                    "time": "10:04",
                    "actor": "operator",
                    "state": "acknowledged",
                    "event": "integration.incident.status_changed",
                    "detail": "Owner acknowledged the integration runbook",
                },
                {
                    "time": "10:11",
                    "actor": "operator",
                    "state": "mitigating",
                    "event": "runbook.mitigation.started",
                    "detail": "Mapping review and retry boundary checked",
                },
                {
                    "time": "10:18",
                    "actor": "system",
                    "state": "recovered",
                    "event": "integration.retry.completed",
                    "detail": "Synthetic retry completed with no production data",
                },
                {
                    "time": "10:22",
                    "actor": "operator",
                    "state": "resolved",
                    "event": "incident.resolved",
                    "detail": "Resolution evidence attached to public-safe record",
                },
            ],
            "recoveryActions": [
                {
                    "name": "Acknowledge",
                    "state": "ready",
                    "owner": "operator",
                    "detail": "Set incident status to acknowledged and keep owner visible",
                    "evidence": "integration.incident.status_changed",
                },
                {
                    "name": "Mitigate",
                    "state": "active",
                    "owner": "integrations",
                    "detail": "Review mapping failure and retry only idempotent operation",
                    "evidence": "outbox.retry.requested",
                },
                {
                    "name": "Verify",
                    "state": "ready",
                    "owner": "platform",
                    "detail": "Confirm metrics, logs, and postcheck evidence before resolve",
                    "evidence": "postcheck.gates.passed",
                },
                {
                    "name": "Resolve",
                    "state": "ready",
                    "owner": "operator",
                    "detail": "Attach public-safe evidence and close incident",
                    "evidence": "incident.resolved",
                },
            ],
            "resolutionEvidence": [
                {
                    "name": "Audit trail",
                    "state": "success",
                    "detail": "Status changes are audited",
                    "evidence": "integration.incident.status_changed",
                },
                {
                    "name": "Metric state",
                    "state": "success",
                    "detail": "Incident counts stay aggregate and label-safe",
                    "evidence": "drivedesk_integration_incidents",
                },
                {
                    "name": "Runbook link",
                    "state": "success",
                    "detail": "Operator has a documented first action",
                    "evidence": "INTEGRATION_INCIDENT_RUNBOOKS.md",
                },
                {
                    "name": "Rollback path",
                    "state": "success",
                    "detail": "Release promotion stays blocked while warning is open",
                    "evidence": "release.canary_gate.blocked",
                },
                {
                    "name": "Postcheck",
                    "state": "success",
                    "detail": "Resolution requires postcheck evidence",
                    "evidence": "postcheck.gates.passed",
                },
            ],
        },
        "businessControlTower": {
            "summary": [
                {
                    "label": "Observed systems",
                    "value": "3",
                    "detail": "crm, bank, accounting",
                    "tone": "blue",
                },
                {
                    "label": "Open exceptions",
                    "value": "1",
                    "detail": "payment state mismatch",
                    "tone": "amber",
                },
                {
                    "label": "Repair actions",
                    "value": "1",
                    "detail": "approval-gated dry-run",
                    "tone": "green",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "public-safe execution",
                    "tone": "violet",
                },
                {
                    "label": "Context cards",
                    "value": "3",
                    "detail": "role workbench preview",
                    "tone": "blue",
                },
                {
                    "label": "Provider intake",
                    "value": "1",
                    "detail": "safe CRM payload preview",
                    "tone": "green",
                },
            ],
            "providerIntake": {
                "providerKey": "crm.bitrix24.mock",
                "sourceType": "crm_deal",
                "subject": "deal:DEAL-2026-001",
                "status": "mapped",
                "summary": (
                    "Bitrix-style deal payload is mapped into a normalized observation "
                    "before DriveDesk builds workbench context."
                ),
                "safePayload": {
                    "amount_bucket": "1000-2000",
                    "owner_role": "sales",
                    "source_state": "invoice_sent",
                },
                "payloadKeys": [
                    "access_token",
                    "amount",
                    "full_name",
                    "owner_role",
                    "phone",
                    "stage",
                ],
                "droppedKeys": [
                    "access_token",
                    "full_name",
                    "phone",
                ],
                "normalizedObservation": {
                    "systemKey": "crm.bitrix24.mock",
                    "systemFamily": "crm",
                    "subject": "deal:DEAL-2026-001",
                    "externalRef": "crm-deal-001",
                    "state": "invoice_sent",
                    "wouldCreate": "BusinessStateObservation",
                    "wouldRecordEvent": "business_state.observation.recorded",
                    "rawPayloadIncluded": False,
                    "piiIncluded": False,
                    "externalFetch": False,
                    "externalMutation": False,
                    "requiresSecret": False,
                },
                "dataBoundaries": [
                    {
                        "name": "preview_only_no_persist",
                        "status": "preview_only",
                        "detail": "Provider intake preview does not create observations or call provider APIs.",
                    },
                    {
                        "name": "raw_provider_payload_not_returned",
                        "status": "clean",
                        "detail": "Only safe fields and dropped key names are returned to the workbench.",
                    },
                    {
                        "name": "secret_boundary",
                        "status": "clean",
                        "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required.",
                    },
                ],
                "nextSteps": [
                    {
                        "step": "record_normalized_observation",
                        "status": "available",
                        "endpoint": "POST /tenants/{tenant_id}/business-state/observations",
                        "externalMutation": False,
                        "evidence": "business_state.observation.recorded",
                    },
                    {
                        "step": "open_workbench_context",
                        "status": "available",
                        "endpoint": "POST /tenants/{tenant_id}/business-workbench-context/preview",
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "step": "run_detection_preview",
                        "status": "available",
                        "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
                        "externalMutation": False,
                        "evidence": "business_detection.previewed",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                },
            },
            "workbenchContext": {
                "contextKind": "role_assist",
                "role": "accountant",
                "riskLevel": "attention",
                "summary": (
                    "DriveDesk turns CRM, bank, and accounting observations into safe "
                    "workbench cards before the accountant decides what to do next."
                ),
                "sourceSystems": [
                    "crm.bitrix24.mock",
                    "bank.statement.mock",
                    "accounting.export.mock",
                ],
                "contextCards": [
                    {
                        "cardId": "crm.deal.DEAL-2026-001.invoice_sent",
                        "title": "CRM deal context",
                        "systemKey": "crm.bitrix24.mock",
                        "systemFamily": "crm",
                        "subject": "deal:DEAL-2026-001",
                        "state": "invoice_sent",
                        "status": "needs_cross_check",
                        "safeFacts": [
                            {"key": "amount_bucket", "value": "1000-2000"},
                            {"key": "owner_role", "value": "sales"},
                        ],
                        "payloadKeys": ["amount_bucket", "owner_role"],
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalFetch": False,
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "cardId": "bank.deal.DEAL-2026-001.paid",
                        "title": "Payment evidence",
                        "systemKey": "bank.statement.mock",
                        "systemFamily": "bank",
                        "subject": "deal:DEAL-2026-001",
                        "state": "paid",
                        "status": "confirmed",
                        "safeFacts": [
                            {"key": "amount_bucket", "value": "1000-2000"},
                            {"key": "matched_by", "value": "payment_reference"},
                        ],
                        "payloadKeys": ["amount_bucket", "matched_by"],
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalFetch": False,
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "cardId": "accounting.deal.DEAL-2026-001.not_exported",
                        "title": "Accounting export context",
                        "systemKey": "accounting.export.mock",
                        "systemFamily": "accounting",
                        "subject": "deal:DEAL-2026-001",
                        "state": "not_exported",
                        "status": "action_required",
                        "safeFacts": [
                            {"key": "export_batch_id", "value": "batch-001"},
                            {"key": "reason", "value": "waiting_for_crm_status"},
                        ],
                        "payloadKeys": ["export_batch_id", "reason"],
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalFetch": False,
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                ],
                "suggestedActions": [
                    {
                        "action": "reconcile_crm_payment_status",
                        "status": "available",
                        "summary": "Compare the paid bank state with the CRM deal state before any external write.",
                        "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
                        "externalMutation": False,
                        "requiresApproval": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "action": "review_accounting_export",
                        "status": "available",
                        "summary": "Open the accounting export evidence and decide whether a dry-run repair is needed.",
                        "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
                        "externalMutation": False,
                        "requiresApproval": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "action": "open_action_plan_preview",
                        "status": "ready",
                        "summary": "Turn the current context into ordered operator work inside DriveDesk.",
                        "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
                        "externalMutation": False,
                        "requiresApproval": False,
                        "evidence": "business_action_plan.previewed",
                    },
                ],
                "dataBoundaries": [
                    {
                        "name": "read_only_source_context",
                        "status": "preview_only",
                        "externalFetch": False,
                        "externalMutation": False,
                        "detail": "The preview uses normalized DriveDesk observations and does not call provider APIs.",
                    },
                    {
                        "name": "pii_redaction",
                        "status": "clean",
                        "rawPayloadIncluded": False,
                        "detail": "Cards expose safe facts and payload keys, not raw provider payloads.",
                    },
                    {
                        "name": "secret_boundary",
                        "status": "clean",
                        "requiresSecret": False,
                        "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required for preview.",
                    },
                ],
                "reviewPoints": [
                    {
                        "name": "single_work_surface",
                        "status": "ready",
                        "detail": "External facts are rendered next to the operator workflow inside DriveDesk.",
                    },
                    {
                        "name": "next_action_boundary",
                        "status": "preview_only",
                        "detail": "Suggested actions link only to DriveDesk previews and approval-gated flows.",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview",
                },
            },
            "detection": {
                "ruleSet": "payment_reconciliation",
                "status": "detected",
                "summary": (
                    "Detector reviewed CRM, bank, and accounting observations and found "
                    "one payment reconciliation exception candidate."
                ),
                "rules": [
                    {
                        "key": "payment_reconciliation.crm_bank_accounting_mismatch",
                        "status": "active",
                        "if": [
                            "crm.state=invoice_sent",
                            "bank.state=paid",
                            "accounting.state=not_exported",
                        ],
                        "then": [
                            "detect crm_payment_mismatch",
                            "suggest sync_status repair",
                        ],
                    }
                ],
                "detectedExceptions": [
                    {
                        "type": "crm_payment_mismatch",
                        "severity": "warning",
                        "confidence": "high",
                        "subject": "deal:DEAL-2026-001",
                        "wouldCreate": "BusinessException",
                        "evidence": "business_detection.previewed",
                    }
                ],
                "suggestedRepairActions": [
                    {
                        "action": "sync_status",
                        "status": "suggested",
                        "requiresApproval": True,
                        "externalMutation": False,
                        "wouldCreate": "RepairAction",
                        "evidence": "business_detection.previewed",
                    }
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-detections/preview",
                },
            },
            "escalation": {
                "policy": "exception_triage",
                "riskLevel": "attention",
                "summary": "One warning exception is routed to the finance reconciliation queue with a dry-run repair next step.",
                "queues": [
                    {
                        "queue": "finance_reconciliation",
                        "ownerRole": "accountant",
                        "openItems": 1,
                        "highestSeverity": "warning",
                        "minSlaMinutes": 120,
                        "status": "active",
                    }
                ],
                "items": [
                    {
                        "exceptionType": "crm_payment_mismatch",
                        "severity": "warning",
                        "status": "open",
                        "subject": "deal:DEAL-2026-001",
                        "ownerRole": "accountant",
                        "queue": "finance_reconciliation",
                        "escalationLevel": "L2",
                        "slaMinutes": 120,
                        "nextAction": "execute_repair_dry_run",
                        "nextActionStatus": "ready",
                        "externalMutation": False,
                        "evidence": "business_escalation.previewed",
                    }
                ],
                "suggestedActions": [
                    {
                        "action": "execute_repair_dry_run",
                        "status": "ready",
                        "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "externalMutation": False,
                        "evidence": "repair_action.approved",
                    }
                ],
                "reviewPoints": [
                    {
                        "name": "write_boundary",
                        "status": "preview_only",
                        "detail": "Escalation does not create tasks, approve repairs, or mutate external systems.",
                    },
                    {
                        "name": "owner_routing",
                        "status": "ready",
                        "detail": "Exception type and severity map to role, queue, and SLA.",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-escalations/preview",
                },
            },
            "actionPlan": {
                "planKind": "exception_resolution",
                "role": "accountant",
                "riskLevel": "attention",
                "summary": "The accountant gets one ordered work plan from CRM, bank, accounting, exception, and repair evidence.",
                "lanes": [
                    {
                        "lane": "finance_reconciliation",
                        "ownerRole": "accountant",
                        "slaMinutes": 120,
                        "workItems": 1,
                        "status": "active",
                    }
                ],
                "steps": [
                    {
                        "sequence": 1,
                        "step": "verify_source_evidence",
                        "lane": "finance_reconciliation",
                        "ownerRole": "accountant",
                        "status": "ready",
                        "summary": "Review CRM, bank, and accounting state before any repair.",
                        "sourceSystems": [
                            "crm.bitrix24.mock",
                            "bank.statement.mock",
                            "accounting.export.mock",
                        ],
                        "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
                        "requiresApproval": False,
                        "externalMutation": False,
                        "evidence": "business_state.observation.recorded",
                    },
                    {
                        "sequence": 2,
                        "step": "execute_repair_dry_run",
                        "lane": "finance_reconciliation",
                        "ownerRole": "accountant",
                        "status": "ready",
                        "summary": "Queue the approved sync_status repair in dry-run mode.",
                        "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "requiresApproval": False,
                        "externalMutation": False,
                        "evidence": "repair_action.approved",
                    },
                    {
                        "sequence": 3,
                        "step": "close_or_acknowledge_exception",
                        "lane": "finance_reconciliation",
                        "ownerRole": "accountant",
                        "status": "waiting_for_repair",
                        "summary": "Record the accountant decision after dry-run evidence is reviewed.",
                        "endpoint": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/status",
                        "requiresApproval": False,
                        "externalMutation": False,
                        "evidence": "business_exception.status_changed",
                    },
                ],
                "automationCandidates": [
                    {
                        "name": "queue_repair_execution",
                        "status": "ready",
                        "action": "execute_repair_dry_run",
                        "adapterKey": "internal.noop",
                        "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "externalMutation": False,
                        "evidence": "repair_action.approved",
                    },
                    {
                        "name": "recheck_accounting_export",
                        "status": "available",
                        "action": "run_read_only_connection_check",
                        "adapterKey": "accounting.export.mock",
                        "endpoint": "POST /tenants/{tenant_id}/integration-connections/{connection_id}/checks",
                        "externalMutation": False,
                        "evidence": "integration_connection.check.requested",
                    },
                ],
                "approvalGates": [
                    {
                        "name": "repair_action_approval",
                        "status": "satisfied",
                        "requiresApproval": True,
                        "externalMutation": False,
                        "evidence": "repair_action.approved",
                    }
                ],
                "reviewPoints": [
                    {
                        "name": "single_work_surface",
                        "status": "ready",
                        "detail": "Cross-system facts become ordered work inside DriveDesk.",
                    },
                    {
                        "name": "approval_boundary",
                        "status": "satisfied",
                        "detail": "External-facing repair remains behind approval and dry-run evidence.",
                    },
                    {
                        "name": "automation_boundary",
                        "status": "preview_only",
                        "detail": "The action plan preview does not create tasks, notify users, or mutate external systems.",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-action-plans/preview",
                },
            },
            "notifications": {
                "notificationKind": "action_plan_updates",
                "role": "accountant",
                "riskLevel": "attention",
                "summary": "DriveDesk prepares safe in-app and Telegram notification drafts from the current action plan.",
                "channels": [
                    {
                        "channel": "in_app",
                        "status": "ready",
                        "configured": True,
                        "externalDelivery": False,
                        "requiresSecret": False,
                        "evidence": "business_notification.previewed",
                    },
                    {
                        "channel": "telegram",
                        "status": "requires_channel_config",
                        "configured": False,
                        "externalDelivery": False,
                        "requiresSecret": True,
                        "evidence": "business_notification.previewed",
                    },
                ],
                "drafts": [
                    {
                        "draftId": "action_plan_updates.in_app.accountant",
                        "channel": "in_app",
                        "recipientRole": "accountant",
                        "title": "Payment mismatch action plan is ready",
                        "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
                        "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "piiIncluded": False,
                        "externalDelivery": False,
                        "status": "ready",
                        "evidence": "business_notification.previewed",
                    },
                    {
                        "draftId": "action_plan_updates.telegram.accountant",
                        "channel": "telegram",
                        "recipientRole": "accountant",
                        "title": "Payment mismatch action plan is ready",
                        "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
                        "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "piiIncluded": False,
                        "externalDelivery": False,
                        "status": "preview_only",
                        "evidence": "business_notification.previewed",
                    },
                ],
                "deliveryPlan": [
                    {
                        "channel": "in_app",
                        "status": "ready",
                        "recipientRole": "accountant",
                        "sendMode": "preview_only",
                        "externalDelivery": False,
                        "requiresSecret": False,
                        "wouldEnqueueEvent": "notification.delivery.requested",
                        "evidence": "business_notification.previewed",
                    },
                    {
                        "channel": "telegram",
                        "status": "requires_channel_config",
                        "recipientRole": "accountant",
                        "sendMode": "preview_only",
                        "externalDelivery": False,
                        "requiresSecret": True,
                        "wouldEnqueueEvent": "notification.delivery.requested",
                        "evidence": "business_notification.previewed",
                    },
                ],
                "approvalGates": [
                    {
                        "name": "notification_content_review",
                        "status": "ready",
                        "requiresApproval": False,
                        "externalDelivery": False,
                        "evidence": "business_notification.previewed",
                    },
                    {
                        "name": "repair_action_approval",
                        "status": "satisfied",
                        "requiresApproval": True,
                        "externalDelivery": False,
                        "evidence": "repair_action.approved",
                    },
                ],
                "reviewPoints": [
                    {
                        "name": "no_external_send",
                        "status": "preview_only",
                        "detail": "Notification preview does not call Telegram, email, CRM, or any other provider.",
                    },
                    {
                        "name": "pii_boundary",
                        "status": "clean",
                        "detail": "Drafts avoid raw personal data and use role, subject key, endpoint, and evidence labels.",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-notifications/preview",
                },
            },
            "briefing": {
                "role": "accountant",
                "riskLevel": "attention",
                "summary": (
                    "Payment is visible in bank evidence, but CRM still shows invoice_sent "
                    "and accounting export is waiting."
                ),
                "sourceSystems": [
                    "crm.bitrix24.mock",
                    "bank.statement.mock",
                    "accounting.export.mock",
                ],
                "highlights": [
                    {
                        "type": "business_exception",
                        "title": "Payment received but CRM and accounting lag behind",
                        "detail": "One open crm_payment_mismatch affects deal:DEAL-2026-001.",
                        "evidence": "business_exception.created",
                    },
                    {
                        "type": "state_observation",
                        "title": "Bank state",
                        "detail": "bank.statement.mock reports paid with matched payment reference.",
                        "evidence": "business_state.observation.recorded",
                    },
                    {
                        "type": "repair_context",
                        "title": "Approved dry-run repair",
                        "detail": "sync_status can queue a dry-run repair event without external mutation.",
                        "evidence": "repair_action.approved",
                    },
                ],
                "recommendedActions": [
                    {
                        "action": "execute_repair_dry_run",
                        "status": "ready",
                        "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
                        "evidence": "repair_action.approved",
                    },
                    {
                        "action": "review_accounting_export",
                        "status": "available",
                        "endpoint": "GET /tenants/{tenant_id}/business-exceptions",
                        "evidence": "accounting.export.mock:not_exported",
                    },
                ],
                "reviewPoints": [
                    {
                        "name": "source_evidence",
                        "status": "ready",
                        "detail": "CRM, bank, and accounting states are visible in one briefing.",
                    },
                    {
                        "name": "external_mutation",
                        "status": "review_required",
                        "detail": "External writes stay behind approval and outbox evidence.",
                    },
                ],
                "api": {
                    "preview": "POST /tenants/{tenant_id}/business-briefings/preview",
                },
            },
            "observations": [
                {
                    "id": "obs-crm-deal",
                    "system": "crm.bitrix24.mock",
                    "subject": "deal:DEAL-2026-001",
                    "state": "invoice_sent",
                    "observedAt": "2026-06-19T06:05:00Z",
                    "evidence": "business_state.observation.recorded",
                },
                {
                    "id": "obs-bank-payment",
                    "system": "bank.statement.mock",
                    "subject": "deal:DEAL-2026-001",
                    "state": "paid",
                    "observedAt": "2026-06-19T06:06:00Z",
                    "evidence": "business_state.observation.recorded",
                },
                {
                    "id": "obs-accounting-export",
                    "system": "accounting.export.mock",
                    "subject": "deal:DEAL-2026-001",
                    "state": "not_exported",
                    "observedAt": "2026-06-19T06:07:00Z",
                    "evidence": "business_state.observation.recorded",
                },
            ],
            "exceptions": [
                {
                    "id": "bex-payment-crm-mismatch",
                    "type": "crm_payment_mismatch",
                    "severity": "warning",
                    "status": "open",
                    "subject": "deal:DEAL-2026-001",
                    "impact": "cash received but CRM and accounting are not aligned",
                    "evidence": "business_exception.created",
                },
            ],
            "repairActions": [
                {
                    "id": "repair-sync-crm-payment",
                    "action": "sync_status",
                    "status": "approved",
                    "safety": "medium",
                    "mode": "dry_run",
                    "requiresApproval": True,
                    "externalMutation": False,
                    "evidence": "repair_action.executed",
                },
            ],
            "flow": [
                {
                    "step": "intake",
                    "owner": "adapter",
                    "state": "preview_only",
                    "detail": "Provider payload is reduced to safe normalized observation fields.",
                    "evidence": "business_provider_intake.previewed",
                },
                {
                    "step": "observe",
                    "owner": "adapter",
                    "state": "done",
                    "detail": "CRM, bank, and accounting states are normalized into one subject.",
                    "evidence": "business_state.observation.recorded",
                },
                {
                    "step": "context",
                    "owner": "workbench",
                    "state": "preview_only",
                    "detail": "Role-specific cards summarize external state without provider reads, secrets, or PII.",
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "step": "detect",
                    "owner": "control_tower",
                    "state": "done",
                    "detail": "Payment state mismatch becomes a business exception with impact.",
                    "evidence": "business_exception.created",
                },
                {
                    "step": "propose",
                    "owner": "repair_engine",
                    "state": "done",
                    "detail": "Repair action is proposed without direct external mutation.",
                    "evidence": "repair_action.proposed",
                },
                {
                    "step": "approve",
                    "owner": "operator",
                    "state": "done",
                    "detail": "Human approval is recorded before execution.",
                    "evidence": "repair_action.approved",
                },
                {
                    "step": "plan",
                    "owner": "workbench",
                    "state": "ready",
                    "detail": "The operator receives an ordered action plan with approval and automation boundaries.",
                    "evidence": "business_action_plan.previewed",
                },
                {
                    "step": "notify",
                    "owner": "workbench",
                    "state": "preview_only",
                    "detail": "DriveDesk prepares notification drafts without external delivery.",
                    "evidence": "business_notification.previewed",
                },
                {
                    "step": "execute",
                    "owner": "outbox",
                    "state": "done",
                    "detail": "Dry-run execution queues a repair event and records result evidence.",
                    "evidence": "repair_action.execution_requested",
                },
            ],
            "api": {
                "intake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                "observe": "POST /tenants/{tenant_id}/business-state/observations",
                "exceptions": "POST /tenants/{tenant_id}/business-exceptions",
                "repair": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
                "approve": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/approve",
                "execute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
            },
            "metrics": [
                "drivedesk_business_state_observations",
                "drivedesk_business_exceptions",
                "drivedesk_repair_actions",
            ],
        },
        "businessIntakePipeline": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
            "summary": [
                {
                    "label": "Provider events",
                    "value": "3",
                    "detail": "CRM, bank, and accounting signals in one preview",
                    "tone": "blue",
                },
                {
                    "label": "Dropped unsafe keys",
                    "value": "5",
                    "detail": "PII and credential markers are removed",
                    "tone": "green",
                },
                {
                    "label": "Detected exceptions",
                    "value": "1",
                    "detail": "payment mismatch candidate",
                    "tone": "amber",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "preview-only pipeline",
                    "tone": "violet",
                },
            ],
            "sourceSystems": [
                "crm.bitrix24.mock",
                "bank.statement.mock",
                "accounting.export.mock",
            ],
            "intakePreviews": [
                {
                    "providerKey": "crm.bitrix24.mock",
                    "sourceType": "crm_deal",
                    "state": "invoice_sent",
                    "safePayload": {
                        "amount_bucket": "1000-2000",
                        "owner_role": "sales",
                        "source_state": "invoice_sent",
                    },
                    "droppedKeys": ["access_token", "full_name", "phone"],
                    "evidence": "business_provider_intake.previewed",
                },
                {
                    "providerKey": "bank.statement.mock",
                    "sourceType": "bank_payment",
                    "state": "paid",
                    "safePayload": {
                        "amount_bucket": "1000-2000",
                        "matched_by": "payment_reference",
                        "source_state": "captured",
                    },
                    "droppedKeys": ["payer_phone"],
                    "evidence": "business_provider_intake.previewed",
                },
                {
                    "providerKey": "accounting.export.mock",
                    "sourceType": "accounting_export",
                    "state": "not_exported",
                    "safePayload": {
                        "export_batch_id": "batch-001",
                        "reason": "waiting_for_crm_status",
                        "source_state": "not_exported",
                    },
                    "droppedKeys": ["session_secret"],
                    "evidence": "business_provider_intake.previewed",
                },
            ],
            "workbench": {
                "role": "accountant",
                "riskLevel": "attention",
                "contextCards": [
                    {
                        "title": "CRM signal",
                        "systemFamily": "crm",
                        "state": "invoice_sent",
                        "status": "needs_cross_check",
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalMutation": False,
                    },
                    {
                        "title": "Bank signal",
                        "systemFamily": "bank",
                        "state": "paid",
                        "status": "confirmed",
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalMutation": False,
                    },
                    {
                        "title": "Accounting signal",
                        "systemFamily": "accounting",
                        "state": "not_exported",
                        "status": "action_required",
                        "rawPayloadIncluded": False,
                        "piiIncluded": False,
                        "externalMutation": False,
                    },
                ],
                "suggestedActions": [
                    {
                        "action": "review_pipeline_detection",
                        "status": "action_required",
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "action": "open_action_plan_preview",
                        "status": "ready",
                        "externalMutation": False,
                        "evidence": "business_action_plan.previewed",
                    },
                ],
            },
            "detections": {
                "status": "detected",
                "ruleSet": "payment_reconciliation",
                "detectedExceptions": [
                    {
                        "exceptionType": "crm_payment_mismatch",
                        "severity": "warning",
                        "subject": "deal:DEAL-2026-001",
                        "wouldCreate": "BusinessException",
                        "externalMutation": False,
                    }
                ],
                "suggestedRepairActions": [
                    {
                        "actionType": "sync_status",
                        "status": "suggested",
                        "requiresApproval": True,
                        "externalMutation": False,
                        "wouldCreate": "RepairAction",
                    }
                ],
            },
            "actionPlan": {
                "riskLevel": "attention",
                "steps": [
                    {
                        "step": "normalize_provider_events",
                        "status": "previewed",
                        "externalMutation": False,
                        "evidence": "business_provider_intake.previewed",
                    },
                    {
                        "step": "open_role_workbench",
                        "status": "ready",
                        "externalMutation": False,
                        "evidence": "business_workbench_context.previewed",
                    },
                    {
                        "step": "review_detected_exceptions",
                        "status": "action_required",
                        "externalMutation": False,
                        "evidence": "business_detection.previewed",
                    },
                    {
                        "step": "prepare_approval_gated_repair",
                        "status": "approval_required",
                        "externalMutation": False,
                        "evidence": "business_action_plan.previewed",
                    },
                ],
                "approvalGates": [
                    {
                        "gate": "external_write_gate",
                        "status": "closed",
                    },
                    {
                        "gate": "notification_delivery_gate",
                        "status": "approval_required",
                    },
                ],
            },
            "notifications": {
                "status": "draft_only",
                "channels": ["in_app", "telegram", "email"],
                "externalDelivery": False,
                "containsPii": False,
                "evidence": "business_notification.previewed",
            },
            "dataBoundaries": [
                {
                    "name": "no_external_calls",
                    "status": "clean",
                    "externalFetch": False,
                    "externalMutation": False,
                },
                {
                    "name": "no_persistence",
                    "status": "preview_only",
                    "externalMutation": False,
                },
                {
                    "name": "secret_and_pii_boundary",
                    "status": "clean",
                    "rawPayloadIncluded": False,
                    "piiIncluded": False,
                    "requiresSecret": False,
                },
            ],
            "api": {
                "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
                "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                "workbenchContext": "POST /tenants/{tenant_id}/business-workbench-context/preview",
                "detections": "POST /tenants/{tenant_id}/business-detections/preview",
                "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
                "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
            },
            "docs": [
                {
                    "label": "Business Intake Pipeline",
                    "path": "docs/public/BUSINESS_INTAKE_PIPELINE.md",
                },
                {
                    "label": "Business Control Tower",
                    "path": "docs/public/BUSINESS_CONTROL_TOWER.md",
                },
                {
                    "label": "API-backed Demo",
                    "path": "docs/public/API_BACKED_DEMO.md",
                },
            ],
        },
        "businessTaskHandoff": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            "summary": [
                {
                    "label": "Task cards",
                    "value": "2",
                    "detail": "internal work preview for accountant",
                    "tone": "blue",
                },
                {
                    "label": "Internal outbox",
                    "value": "2",
                    "detail": "task.created candidates only",
                    "tone": "green",
                },
                {
                    "label": "Draft notifications",
                    "value": "2",
                    "detail": "in-app drafts, no external send",
                    "tone": "amber",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "public preview stays internal",
                    "tone": "violet",
                },
            ],
            "role": "accountant",
            "subject": "deal:DEAL-2026-001",
            "taskCards": [
                {
                    "taskKey": "task.preview.001",
                    "title": "review_detected_exceptions",
                    "assigneeRole": "accountant",
                    "status": "would_create",
                    "priority": "normal",
                    "sourceAction": "review_detected_exceptions",
                    "subject": "deal:DEAL-2026-001",
                    "due": "next_business_day",
                    "wouldCreate": "BusinessRecord(type=task)",
                    "requiresApproval": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_task_handoff.previewed",
                },
                {
                    "taskKey": "task.preview.002",
                    "title": "execute_repair_dry_run",
                    "assigneeRole": "accountant",
                    "status": "would_create",
                    "priority": "high",
                    "sourceAction": "execute_repair_dry_run",
                    "subject": "deal:DEAL-2026-001",
                    "due": "same_day",
                    "wouldCreate": "BusinessRecord(type=task)",
                    "requiresApproval": True,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_task_handoff.previewed",
                },
            ],
            "outboxCandidates": [
                {
                    "eventType": "task.created",
                    "adapterKey": "internal.noop",
                    "status": "would_enqueue",
                    "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-001",
                    "payloadProfile": "safe_task_reference",
                    "sourceAction": "review_detected_exceptions",
                    "containsPii": False,
                    "externalMutation": False,
                    "evidence": "business_task_handoff.previewed",
                },
                {
                    "eventType": "task.created",
                    "adapterKey": "internal.noop",
                    "status": "would_enqueue",
                    "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-002",
                    "payloadProfile": "safe_task_reference",
                    "sourceAction": "execute_repair_dry_run",
                    "containsPii": False,
                    "externalMutation": False,
                    "evidence": "business_task_handoff.previewed",
                },
            ],
            "notificationDrafts": [
                {
                    "draftId": "task_handoff.in_app.accountant.001",
                    "channel": "in_app",
                    "recipientRole": "accountant",
                    "title": "Task handoff ready",
                    "body": "deal:DEAL-2026-001 has internal task preview: review_detected_exceptions.",
                    "status": "draft_only",
                    "externalDelivery": False,
                    "containsPii": False,
                    "requiresSecret": False,
                    "evidence": "business_task_handoff.previewed",
                },
                {
                    "draftId": "task_handoff.in_app.accountant.002",
                    "channel": "in_app",
                    "recipientRole": "accountant",
                    "title": "Task handoff ready",
                    "body": "deal:DEAL-2026-001 has internal task preview: execute_repair_dry_run.",
                    "status": "draft_only",
                    "externalDelivery": False,
                    "containsPii": False,
                    "requiresSecret": False,
                    "evidence": "business_task_handoff.previewed",
                },
            ],
            "approvalGates": [
                {
                    "gate": "task_creation_review",
                    "status": "required",
                    "requiresApproval": False,
                    "externalMutation": False,
                },
                {
                    "gate": "external_write_gate",
                    "status": "closed",
                    "requiresApproval": True,
                    "externalMutation": False,
                },
                {
                    "gate": "repair_action_approval",
                    "status": "required",
                    "requiresApproval": True,
                    "externalMutation": False,
                },
            ],
            "dataBoundaries": [
                {
                    "name": "preview_only_no_persistence",
                    "status": "preview_only",
                    "externalMutation": False,
                },
                {
                    "name": "internal_only_outbox",
                    "status": "clean",
                    "adapterKey": "internal.noop",
                    "externalMutation": False,
                },
                {
                    "name": "safe_task_payload",
                    "status": "clean",
                    "rawPayloadIncluded": False,
                    "piiIncluded": False,
                    "containsPii": False,
                },
            ],
            "api": {
                "preview": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
                "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
                "workflowRules": "POST /tenants/{tenant_id}/workflow-rules",
                "taskRecords": "POST /tenants/{tenant_id}/business-records",
            },
            "docs": [
                {
                    "label": "Business Task Handoff",
                    "path": "docs/public/BUSINESS_TASK_HANDOFF.md",
                },
                {
                    "label": "Workflow Demo",
                    "path": "docs/public/WORKFLOW_DEMO.md",
                },
                {
                    "label": "Business Intake Pipeline",
                    "path": "docs/public/BUSINESS_INTAKE_PIPELINE.md",
                },
            ],
        },
        "businessNotificationChannels": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-notification-channels/preview",
            "summary": [
                {
                    "label": "Channels",
                    "value": "5",
                    "detail": "in-app, Telegram, email, SMS, webhook",
                    "tone": "blue",
                },
                {
                    "label": "Internal ready",
                    "value": "1",
                    "detail": "in-app can stay inside DriveDesk",
                    "tone": "green",
                },
                {
                    "label": "Draft-only external",
                    "value": "4",
                    "detail": "private connector setup required",
                    "tone": "amber",
                },
                {
                    "label": "External deliveries",
                    "value": "0",
                    "detail": "public preview sends nothing",
                    "tone": "violet",
                },
            ],
            "role": "accountant",
            "subject": "deal:DEAL-2026-001",
            "channels": [
                {
                    "channel": "in_app",
                    "status": "ready",
                    "configured": True,
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "destinationProfile": "internal_user_inbox",
                    "sendMode": "internal_preview",
                    "readiness": "usable_for_internal_work",
                    "externalDelivery": False,
                    "requiresSecret": False,
                    "requiresPrivateConnector": False,
                    "externalProviderMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "safePayloadProfile": "role_subject_action_reference",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "channel": "telegram",
                    "status": "requires_private_secret",
                    "configured": False,
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "destinationProfile": "telegram_bot_chat",
                    "sendMode": "draft_only",
                    "readiness": "private_connector_needed",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "requiresPrivateConnector": True,
                    "externalProviderMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "safePayloadProfile": "role_subject_action_reference",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "channel": "email",
                    "status": "requires_private_secret",
                    "configured": False,
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "destinationProfile": "smtp_or_provider_template",
                    "sendMode": "draft_only",
                    "readiness": "private_connector_needed",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "requiresPrivateConnector": True,
                    "externalProviderMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "safePayloadProfile": "role_subject_action_reference",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "channel": "sms",
                    "status": "requires_private_provider",
                    "configured": False,
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "destinationProfile": "sms_provider_template",
                    "sendMode": "draft_only",
                    "readiness": "provider_contract_needed",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "requiresPrivateConnector": True,
                    "externalProviderMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "safePayloadProfile": "role_subject_action_reference",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "channel": "webhook",
                    "status": "requires_private_endpoint",
                    "configured": False,
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "destinationProfile": "signed_webhook_endpoint",
                    "sendMode": "draft_only",
                    "readiness": "endpoint_and_signing_key_needed",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "requiresPrivateConnector": True,
                    "externalProviderMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "safePayloadProfile": "role_subject_action_reference",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
            ],
            "routingRules": [
                {
                    "rule": "prefer_internal_in_app",
                    "status": "ready",
                    "channel": "in_app",
                    "detail": "Internal work notifications can be represented without external delivery.",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "rule": "external_channels_require_private_connector",
                    "status": "required",
                    "channelCount": 4,
                    "detail": "External delivery stays behind private connector and secret setup.",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "rule": "safe_payload_only",
                    "status": "clean",
                    "payloadProfile": "role_subject_action_reference",
                    "detail": "Drafts use role, subject key, action reference, and evidence labels only.",
                    "evidence": "business_notification_channel_matrix.previewed",
                },
            ],
            "deliveryDrafts": [
                {
                    "draftId": "channel_matrix.in_app.accountant",
                    "channel": "in_app",
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "title": "DriveDesk action update",
                    "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
                    "status": "ready",
                    "sendMode": "internal_preview",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "safePayloadProfile": "role_subject_action_reference",
                    "externalDelivery": False,
                    "requiresSecret": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "draftId": "channel_matrix.telegram.accountant",
                    "channel": "telegram",
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "title": "DriveDesk action update",
                    "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
                    "status": "draft_only",
                    "sendMode": "draft_only",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "safePayloadProfile": "role_subject_action_reference",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "draftId": "channel_matrix.email.accountant",
                    "channel": "email",
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "title": "DriveDesk action update",
                    "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
                    "status": "draft_only",
                    "sendMode": "draft_only",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "safePayloadProfile": "role_subject_action_reference",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "draftId": "channel_matrix.sms.accountant",
                    "channel": "sms",
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "title": "DriveDesk action update",
                    "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
                    "status": "draft_only",
                    "sendMode": "draft_only",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "safePayloadProfile": "role_subject_action_reference",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "draftId": "channel_matrix.webhook.accountant",
                    "channel": "webhook",
                    "recipientRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "title": "DriveDesk action update",
                    "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
                    "status": "draft_only",
                    "sendMode": "draft_only",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "safePayloadProfile": "role_subject_action_reference",
                    "externalDelivery": False,
                    "requiresSecret": True,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
            ],
            "approvalGates": [
                {
                    "gate": "notification_content_review",
                    "status": "ready",
                    "requiresApproval": False,
                    "externalDelivery": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "gate": "private_channel_secret_setup",
                    "status": "required",
                    "requiresApproval": True,
                    "externalDelivery": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
                {
                    "gate": "external_delivery_gate",
                    "status": "closed",
                    "requiresApproval": True,
                    "externalDelivery": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
            ],
            "dataBoundaries": [
                {
                    "name": "preview_only_no_delivery",
                    "status": "preview_only",
                    "externalDelivery": False,
                    "externalProviderMutation": False,
                },
                {
                    "name": "server_secret_store_boundary",
                    "status": "documented",
                    "requiresSecret": True,
                    "browserTokenStorage": False,
                },
                {
                    "name": "safe_notification_payload",
                    "status": "clean",
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                },
            ],
            "api": {
                "preview": "POST /tenants/{tenant_id}/business-notification-channels/preview",
                "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
                "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            },
            "docs": [
                {
                    "label": "Business Notification Channels",
                    "path": "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md",
                },
                {
                    "label": "Business Task Handoff",
                    "path": "docs/public/BUSINESS_TASK_HANDOFF.md",
                },
                {
                    "label": "API-backed Demo",
                    "path": "docs/public/API_BACKED_DEMO.md",
                },
            ],
        },
        "businessContextAssistant": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-workbench-context/preview",
            "summary": [
                {
                    "label": "Context cards",
                    "value": "4",
                    "detail": "CRM, bank, accounting, legal reference",
                    "tone": "blue",
                },
                {
                    "label": "Source systems",
                    "value": "4",
                    "detail": "safe facts normalized into one work surface",
                    "tone": "green",
                },
                {
                    "label": "Suggested actions",
                    "value": "4",
                    "detail": "operator-review and draft-only next steps",
                    "tone": "amber",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "context preview never mutates providers",
                    "tone": "violet",
                },
            ],
            "role": "accountant",
            "subject": "deal:DEAL-2026-001",
            "sourceSystems": [
                "crm.bitrix24.mock",
                "bank.statement.mock",
                "accounting.export.mock",
                "legal.reference.mock",
            ],
            "contextCards": [
                {
                    "id": "context.crm.deal-state",
                    "title": "CRM deal state",
                    "sourceSystem": "crm.bitrix24.mock",
                    "systemFamily": "crm",
                    "status": "attention",
                    "safeFact": "invoice_sent",
                    "reason": "CRM stage expects payment confirmation before accounting export.",
                    "externalFetch": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "id": "context.bank.payment-evidence",
                    "title": "Bank payment evidence",
                    "sourceSystem": "bank.statement.mock",
                    "systemFamily": "bank",
                    "status": "ready",
                    "safeFact": "amount_bucket:1000-2000",
                    "reason": "Bank statement has a matching amount bucket but no raw payer details are exposed.",
                    "externalFetch": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "id": "context.accounting.export-gap",
                    "title": "Accounting export gap",
                    "sourceSystem": "accounting.export.mock",
                    "systemFamily": "accounting",
                    "status": "action_required",
                    "safeFact": "export_pending",
                    "reason": "Payment can be reconciled before the accounting export is queued.",
                    "externalFetch": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "id": "context.legal.policy-reference",
                    "title": "Policy reference",
                    "sourceSystem": "legal.reference.mock",
                    "systemFamily": "legal",
                    "status": "documented",
                    "safeFact": "payment_status_note_template",
                    "reason": "The operator gets a template reference, not copied legal text or external account data.",
                    "externalFetch": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "fullTextIncluded": False,
                    "evidence": "business_workbench_context.previewed",
                },
            ],
            "insightRules": [
                {
                    "rule": "correlate_payment_evidence",
                    "status": "ready",
                    "sources": ["crm.bitrix24.mock", "bank.statement.mock"],
                    "result": "bank amount bucket can support CRM payment review",
                    "externalMutation": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "rule": "detect_accounting_export_gap",
                    "status": "attention",
                    "sources": ["accounting.export.mock"],
                    "result": "accounting export remains pending until operator review",
                    "externalMutation": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "rule": "attach_policy_reference",
                    "status": "documented",
                    "sources": ["legal.reference.mock"],
                    "result": "operator sees a policy/template reference without copied external content",
                    "externalMutation": False,
                    "fullTextIncluded": False,
                    "evidence": "business_workbench_context.previewed",
                },
            ],
            "suggestedActions": [
                {
                    "action": "open_reconciliation_plan",
                    "status": "recommended",
                    "mode": "operator_review",
                    "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
                    "externalMutation": False,
                    "requiresApproval": False,
                    "evidence": "business_action_plan.previewed",
                },
                {
                    "action": "queue_accounting_export_after_review",
                    "status": "approval_required",
                    "mode": "approval_required",
                    "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
                    "externalMutation": False,
                    "requiresApproval": True,
                    "evidence": "accounting.export.requested",
                },
                {
                    "action": "attach_policy_reference",
                    "status": "ready",
                    "mode": "internal_reference",
                    "endpoint": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
                    "externalMutation": False,
                    "requiresApproval": False,
                    "evidence": "business_workbench_context.previewed",
                },
                {
                    "action": "prepare_internal_notification",
                    "status": "draft_only",
                    "mode": "draft_only",
                    "endpoint": "POST /tenants/{tenant_id}/business-notification-channels/preview",
                    "externalMutation": False,
                    "requiresApproval": False,
                    "evidence": "business_notification_channel_matrix.previewed",
                },
            ],
            "dataBoundaries": [
                {
                    "name": "read_only_context_preview",
                    "status": "preview_only",
                    "externalFetch": False,
                    "externalMutation": False,
                },
                {
                    "name": "no_raw_provider_payload",
                    "status": "clean",
                    "rawPayloadIncluded": False,
                    "containsPii": False,
                },
                {
                    "name": "secret_boundary",
                    "status": "clean",
                    "requiresSecret": False,
                    "browserTokenStorage": False,
                },
                {
                    "name": "legal_reference_link_only",
                    "status": "documented",
                    "fullTextIncluded": False,
                    "externalAccountDataIncluded": False,
                },
            ],
            "api": {
                "standalone": "GET /demo/business-context-assistant",
                "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview",
                "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
                "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            },
            "docs": [
                {
                    "label": "Business Context Assistant",
                    "path": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
                },
                {
                    "label": "Business Control Tower",
                    "path": "docs/public/BUSINESS_CONTROL_TOWER.md",
                },
                {
                    "label": "Provider Connector Guide",
                    "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
                },
            ],
        },
        "businessActionExecution": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-action-executions/preview",
            "summary": [
                {
                    "label": "Execution plans",
                    "value": "3",
                    "detail": "review, accounting export, notification",
                    "tone": "blue",
                },
                {
                    "label": "Preflight checks",
                    "value": "4",
                    "detail": "payload, idempotency, approval, secrets",
                    "tone": "green",
                },
                {
                    "label": "Approval gates",
                    "value": "3",
                    "detail": "operator review and provider write boundaries",
                    "tone": "amber",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "dry-run preview sends nothing",
                    "tone": "violet",
                },
            ],
            "role": "accountant",
            "subject": "deal:DEAL-2026-001",
            "executionPlan": [
                {
                    "executionKey": "execution.preview.001",
                    "action": "open_reconciliation_plan",
                    "status": "dry_run_ready",
                    "mode": "dry_run",
                    "adapterKey": "internal.noop",
                    "wouldEnqueueEvent": "business.action.review_requested",
                    "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:open_reconciliation_plan:001",
                    "safePayloadProfile": "role_subject_action_reference",
                    "dryRun": True,
                    "safeToAutoRun": True,
                    "requiresApproval": False,
                    "commitWouldMutateProvider": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "executionKey": "execution.preview.002",
                    "action": "queue_accounting_export_after_review",
                    "status": "approval_required",
                    "mode": "dry_run",
                    "adapterKey": "accounting.export.mock",
                    "wouldEnqueueEvent": "accounting.export.requested",
                    "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:queue_accounting_export_after_review:002",
                    "safePayloadProfile": "role_subject_action_reference",
                    "dryRun": True,
                    "safeToAutoRun": False,
                    "requiresApproval": True,
                    "commitWouldMutateProvider": True,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "executionKey": "execution.preview.003",
                    "action": "prepare_internal_notification",
                    "status": "dry_run_ready",
                    "mode": "dry_run",
                    "adapterKey": "internal.notification",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:prepare_internal_notification:003",
                    "safePayloadProfile": "role_subject_action_reference",
                    "dryRun": True,
                    "safeToAutoRun": True,
                    "requiresApproval": False,
                    "commitWouldMutateProvider": False,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
            ],
            "preflightChecks": [
                {
                    "check": "safe_payload_profile",
                    "status": "passed",
                    "detail": "Only role, subject key, action key, and evidence references are included.",
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "check": "idempotency_key_ready",
                    "status": "passed",
                    "detail": "Every execution candidate has a deterministic idempotency key.",
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "check": "approval_gate_attached",
                    "status": "required",
                    "detail": "Provider-changing commits stay behind operator approval.",
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "check": "connector_secret_boundary",
                    "status": "clean",
                    "detail": "Preview does not require credentials or browser token storage.",
                    "externalMutation": False,
                    "requiresSecret": False,
                    "browserTokenStorage": False,
                    "evidence": "business_action_execution.previewed",
                },
            ],
            "dryRunResults": [
                {
                    "resultKey": "dry_run.001",
                    "action": "open_reconciliation_plan",
                    "status": "would_enqueue",
                    "wouldRecord": "WorkflowActionRun",
                    "wouldEnqueueEvent": "business.action.review_requested",
                    "adapterKey": "internal.noop",
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "resultKey": "dry_run.002",
                    "action": "queue_accounting_export_after_review",
                    "status": "would_enqueue",
                    "wouldRecord": "WorkflowActionRun",
                    "wouldEnqueueEvent": "accounting.export.requested",
                    "adapterKey": "accounting.export.mock",
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "resultKey": "dry_run.003",
                    "action": "prepare_internal_notification",
                    "status": "would_enqueue",
                    "wouldRecord": "WorkflowActionRun",
                    "wouldEnqueueEvent": "notification.delivery.requested",
                    "adapterKey": "internal.notification",
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_action_execution.previewed",
                },
            ],
            "approvalGates": [
                {
                    "gate": "operator_review_gate",
                    "status": "required",
                    "requiresApproval": True,
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "gate": "external_write_gate",
                    "status": "closed",
                    "requiresApproval": True,
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
                {
                    "gate": "idempotent_outbox_gate",
                    "status": "ready",
                    "requiresApproval": False,
                    "externalMutation": False,
                    "evidence": "business_action_execution.previewed",
                },
            ],
            "rollbackPlan": [
                {
                    "step": "preview_has_no_rollback",
                    "status": "not_needed",
                    "detail": "Dry-run preview writes nothing and has no external state to roll back.",
                    "externalMutation": False,
                },
                {
                    "step": "commit_uses_outbox_recovery",
                    "status": "documented",
                    "detail": "Future commit execution uses outbox retry, dead-letter review, and audit evidence.",
                    "externalMutation": False,
                },
            ],
            "dataBoundaries": [
                {
                    "name": "dry_run_only",
                    "status": "preview_only",
                    "externalMutation": False,
                },
                {
                    "name": "no_provider_write",
                    "status": "closed",
                    "externalMutation": False,
                },
                {
                    "name": "safe_execution_payload",
                    "status": "clean",
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                },
                {
                    "name": "audit_and_outbox_contract",
                    "status": "documented",
                    "externalMutation": False,
                },
            ],
            "api": {
                "standalone": "GET /demo/business-action-execution",
                "preview": "POST /tenants/{tenant_id}/business-action-executions/preview",
                "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
                "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
                "repairExecute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
            },
            "docs": [
                {
                    "label": "Business Action Execution",
                    "path": "docs/public/BUSINESS_ACTION_EXECUTION.md",
                },
                {
                    "label": "Business Task Handoff",
                    "path": "docs/public/BUSINESS_TASK_HANDOFF.md",
                },
                {
                    "label": "Business Context Assistant",
                    "path": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
                },
            ],
        },
        "businessApprovalGateway": {
            "status": "previewed",
            "command": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
            "summary": [
                {
                    "label": "Approval requests",
                    "value": "1",
                    "detail": "provider-changing commit candidate",
                    "tone": "amber",
                },
                {
                    "label": "Policy checks",
                    "value": "4",
                    "detail": "RBAC, dual control, idempotency, write lock",
                    "tone": "green",
                },
                {
                    "label": "Commit unlocks",
                    "value": "1",
                    "detail": "blocked until approved",
                    "tone": "blue",
                },
                {
                    "label": "Provider writes",
                    "value": "0",
                    "detail": "approval preview unlocks nothing",
                    "tone": "violet",
                },
            ],
            "role": "accountant",
            "subject": "deal:DEAL-2026-001",
            "approvalRequests": [
                {
                    "approvalKey": "approval.preview.001",
                    "action": "queue_accounting_export_after_review",
                    "status": "approval_required",
                    "requesterRole": "accountant",
                    "approverRole": "owner",
                    "subject": "deal:DEAL-2026-001",
                    "idempotencyKey": (
                        "business-approval-gateway:deal:DEAL-2026-001:"
                        "queue_accounting_export_after_review:001"
                    ),
                    "sourceIdempotencyKey": (
                        "business-action-execution:deal:DEAL-2026-001:"
                        "queue_accounting_export_after_review:002"
                    ),
                    "requiresDualControl": True,
                    "commitWouldMutateProvider": True,
                    "externalMutation": False,
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                    "evidence": "business_approval_gateway.previewed",
                },
            ],
            "policyChecks": [
                {
                    "check": "rbac_approver_role",
                    "status": "passed",
                    "detail": "Approver role is allowed to review provider-changing commits.",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "check": "dual_control_required",
                    "status": "required",
                    "detail": "Requester and approver stay separated before commit unlock.",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "check": "idempotency_preserved",
                    "status": "passed",
                    "detail": "Approval request keeps source and approval idempotency keys.",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "check": "provider_write_closed_until_approval",
                    "status": "closed",
                    "detail": "Provider write stays locked until approval is recorded.",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
            ],
            "approverRouting": [
                {
                    "route": "owner_or_accountant_review",
                    "status": "ready",
                    "queue": "approval.review",
                    "ownerRole": "owner",
                    "slaMinutes": 120,
                    "notificationChannel": "in_app",
                    "externalDelivery": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "route": "escalate_if_sla_missed",
                    "status": "armed",
                    "queue": "approval.escalation",
                    "ownerRole": "owner",
                    "slaMinutes": 240,
                    "notificationChannel": "in_app",
                    "externalDelivery": False,
                    "evidence": "business_approval_gateway.previewed",
                },
            ],
            "commitUnlocks": [
                {
                    "unlockKey": "commit.unlock.001",
                    "action": "queue_accounting_export_after_review",
                    "status": "blocked_until_approved",
                    "wouldRecord": "WorkflowActionRun",
                    "wouldEnqueueEvent": "business.action.approval_granted",
                    "outboxReady": True,
                    "providerWriteUnlocked": False,
                    "externalMutation": False,
                    "rollbackAttached": True,
                    "evidence": "business_approval_gateway.previewed",
                },
            ],
            "auditTrail": [
                {
                    "event": "business_approval.requested",
                    "status": "would_record",
                    "actorRole": "accountant",
                    "subject": "deal:DEAL-2026-001",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "event": "business_approval.policy_checked",
                    "status": "would_record",
                    "actorRole": "system",
                    "subject": "deal:DEAL-2026-001",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
                {
                    "event": "business_approval.commit_unlocked",
                    "status": "blocked_until_approved",
                    "actorRole": "owner",
                    "subject": "deal:DEAL-2026-001",
                    "externalMutation": False,
                    "evidence": "business_approval_gateway.previewed",
                },
            ],
            "dataBoundaries": [
                {
                    "name": "preview_only_no_approval_record",
                    "status": "preview_only",
                    "externalMutation": False,
                },
                {
                    "name": "provider_write_locked",
                    "status": "closed",
                    "externalMutation": False,
                },
                {
                    "name": "rbac_dual_control",
                    "status": "enforced",
                    "externalMutation": False,
                },
                {
                    "name": "safe_approval_payload",
                    "status": "clean",
                    "containsPii": False,
                    "rawPayloadIncluded": False,
                },
            ],
            "api": {
                "standalone": "GET /demo/business-approval-gateway",
                "preview": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
                "actionExecution": "POST /tenants/{tenant_id}/business-action-executions/preview",
                "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            },
            "docs": [
                {
                    "label": "Business Approval Gateway",
                    "path": "docs/public/BUSINESS_APPROVAL_GATEWAY.md",
                },
                {
                    "label": "Business Action Execution",
                    "path": "docs/public/BUSINESS_ACTION_EXECUTION.md",
                },
                {
                    "label": "Business Task Handoff",
                    "path": "docs/public/BUSINESS_TASK_HANDOFF.md",
                },
            ],
        },
        "businessScenarioReplay": {
            "status": "validated",
            "command": "bash scripts/check_public_business_scenario_replay.sh",
            "summary": [
                {
                    "label": "Scenario groups",
                    "value": "3",
                    "detail": "CRM, support, and procurement replay paths",
                    "tone": "blue",
                },
                {
                    "label": "Source systems",
                    "value": "7",
                    "detail": "external signals normalized before action",
                    "tone": "green",
                },
                {
                    "label": "Operator actions",
                    "value": "8",
                    "detail": "recommended actions stay approval-aware",
                    "tone": "amber",
                },
                {
                    "label": "External writes",
                    "value": "0",
                    "detail": "public replay is read-only",
                    "tone": "violet",
                },
            ],
            "scenarios": [
                {
                    "id": "crm-bank-payment-mismatch",
                    "title": "CRM and bank payment mismatch",
                    "status": "attention",
                    "riskLevel": "warning",
                    "operatorRole": "accountant",
                    "trigger": "crm.deal.updated",
                    "decision": "open reconciliation workbench",
                    "sourceSystems": [
                        "crm.bitrix24.mock",
                        "bank.statement.mock",
                        "accounting.export.mock",
                    ],
                    "normalizedFacts": [
                        {
                            "key": "crm_stage",
                            "value": "invoice_sent",
                            "source": "crm.bitrix24.mock",
                        },
                        {
                            "key": "bank_status",
                            "value": "payment_seen",
                            "source": "bank.statement.mock",
                        },
                        {
                            "key": "accounting_status",
                            "value": "export_pending",
                            "source": "accounting.export.mock",
                        },
                    ],
                    "recommendedActions": [
                        {
                            "action": "compare bank amount bucket with CRM deal amount",
                            "mode": "operator_review",
                            "evidence": "integration.reconciliation.previewed",
                        },
                        {
                            "action": "queue accounting export after approval",
                            "mode": "approval_required",
                            "evidence": "business_action_plan.previewed",
                        },
                        {
                            "action": "prepare customer payment-status note",
                            "mode": "draft_only",
                            "evidence": "business_notification.previewed",
                        },
                    ],
                    "automationCandidates": [
                        {
                            "candidate": "create business exception",
                            "safeToAutoRun": True,
                            "boundary": "internal_record_only",
                        },
                        {
                            "candidate": "send customer notification",
                            "safeToAutoRun": False,
                            "boundary": "requires_operator_approval",
                        },
                    ],
                    "evidence": [
                        "business_exception.created",
                        "business_action_plan.previewed",
                        "integration.reconciliation.recorded",
                    ],
                    "dataBoundary": [
                        "no raw provider payload",
                        "no credentials",
                        "no personal data",
                        "synthetic sources",
                    ],
                },
                {
                    "id": "support-sla-risk",
                    "title": "Support SLA risk",
                    "status": "action_required",
                    "riskLevel": "high",
                    "operatorRole": "support_lead",
                    "trigger": "support.message.received",
                    "decision": "escalate with context before SLA breach",
                    "sourceSystems": [
                        "support.inbox.mock",
                        "telephony.callback.mock",
                        "sla.policy.mock",
                    ],
                    "normalizedFacts": [
                        {
                            "key": "message_state",
                            "value": "waiting_for_reply",
                            "source": "support.inbox.mock",
                        },
                        {
                            "key": "callback_state",
                            "value": "missed",
                            "source": "telephony.callback.mock",
                        },
                        {
                            "key": "sla_window",
                            "value": "15m",
                            "source": "sla.policy.mock",
                        },
                    ],
                    "recommendedActions": [
                        {
                            "action": "assign support lead and create reply task",
                            "mode": "operator_review",
                            "evidence": "business_escalation.previewed",
                        },
                        {
                            "action": "prepare apology and callback draft",
                            "mode": "draft_only",
                            "evidence": "business_notification.previewed",
                        },
                    ],
                    "automationCandidates": [
                        {
                            "candidate": "open escalation item",
                            "safeToAutoRun": True,
                            "boundary": "internal_record_only",
                        },
                        {
                            "candidate": "place callback",
                            "safeToAutoRun": False,
                            "boundary": "external_channel_blocked",
                        },
                    ],
                    "evidence": [
                        "business_escalation.previewed",
                        "business_action_plan.previewed",
                        "business_notification.previewed",
                    ],
                    "dataBoundary": [
                        "message body omitted",
                        "phone number omitted",
                        "no external delivery",
                        "synthetic sources",
                    ],
                },
                {
                    "id": "procurement-delay-risk",
                    "title": "Procurement delay risk",
                    "status": "needs_cross_check",
                    "riskLevel": "medium",
                    "operatorRole": "operations_manager",
                    "trigger": "supplier.delivery.updated",
                    "decision": "create procurement exception and check cash timing",
                    "sourceSystems": [
                        "supplier.portal.mock",
                        "inventory.stock.mock",
                        "bank.payment-order.mock",
                    ],
                    "normalizedFacts": [
                        {
                            "key": "supplier_state",
                            "value": "delayed",
                            "source": "supplier.portal.mock",
                        },
                        {
                            "key": "stock_state",
                            "value": "below_minimum",
                            "source": "inventory.stock.mock",
                        },
                        {
                            "key": "payment_order",
                            "value": "prepared",
                            "source": "bank.payment-order.mock",
                        },
                    ],
                    "recommendedActions": [
                        {
                            "action": "open procurement exception",
                            "mode": "operator_review",
                            "evidence": "business_exception.created",
                        },
                        {
                            "action": "compare supplier ETA with minimum stock window",
                            "mode": "operator_review",
                            "evidence": "business_workbench_context.previewed",
                        },
                        {
                            "action": "hold payment order until manager approval",
                            "mode": "approval_required",
                            "evidence": "business_action_plan.previewed",
                        },
                    ],
                    "automationCandidates": [
                        {
                            "candidate": "create manager task",
                            "safeToAutoRun": True,
                            "boundary": "internal_record_only",
                        },
                        {
                            "candidate": "release bank payment",
                            "safeToAutoRun": False,
                            "boundary": "financial_write_blocked",
                        },
                    ],
                    "evidence": [
                        "business_exception.created",
                        "business_workbench_context.previewed",
                        "business_action_plan.previewed",
                    ],
                    "dataBoundary": [
                        "no bank credentials",
                        "no supplier raw payload",
                        "payment values bucketed",
                        "synthetic sources",
                    ],
                },
            ],
            "flow": [
                {
                    "step": "1",
                    "stage": "signal",
                    "detail": "External systems produce signals through adapters, files, webhooks, or polling.",
                    "evidence": "provider_signal.received",
                },
                {
                    "step": "2",
                    "stage": "normalize",
                    "detail": "DriveDesk maps each signal into safe business facts with provider-specific details removed.",
                    "evidence": "business_state.observation.recorded",
                },
                {
                    "step": "3",
                    "stage": "detect",
                    "detail": "Rules compare facts across systems and create exception candidates.",
                    "evidence": "business_exception.created",
                },
                {
                    "step": "4",
                    "stage": "plan",
                    "detail": "The workbench builds role-specific context, recommended actions, and approval gates.",
                    "evidence": "business_action_plan.previewed",
                },
                {
                    "step": "5",
                    "stage": "execute",
                    "detail": "Only approved internal actions can run; external writes stay behind explicit approval.",
                    "evidence": "operator_approval.required",
                },
            ],
            "docs": [
                {
                    "label": "Business Scenario Replay",
                    "path": "docs/public/BUSINESS_SCENARIO_REPLAY.md",
                },
                {
                    "label": "Business Control Tower",
                    "path": "docs/public/BUSINESS_CONTROL_TOWER.md",
                },
                {
                    "label": "API Backed Demo",
                    "path": "docs/public/API_BACKED_DEMO.md",
                },
                {
                    "label": "Technical Capability Map",
                    "path": "docs/public/TECHNICAL_CAPABILITY_MAP.md",
                },
            ],
        },
        "recoveryEvidence": [
            {
                "name": "Synthetic backup",
                "state": "success",
                "detail": "temporary SQLite backup artifact created",
                "evidence": "backup_sha256_recorded",
            },
            {
                "name": "Restore drill",
                "state": "success",
                "detail": "restored into a separate temporary database",
                "evidence": "restore_integrity_ok",
            },
            {
                "name": "Schema contract",
                "state": "success",
                "detail": "core tables and row counts matched after restore",
                "evidence": "counts_match",
            },
            {
                "name": "Data boundary",
                "state": "success",
                "detail": "synthetic demo data only",
                "evidence": "production_data_touched_false",
            },
            {
                "name": "Release rollback",
                "state": "success",
                "detail": "bad candidate release rolled back to stable",
                "evidence": "release.rollback.executed",
            },
            {
                "name": "Stable after rollback",
                "state": "success",
                "detail": "stable release healthy after rollback",
                "evidence": "stable_release_healthy_after_rollback",
            },
            {
                "name": "SLO canary gate",
                "state": "success",
                "detail": "candidate release blocked before promotion",
                "evidence": "release.canary_gate.blocked",
            },
            {
                "name": "Promotion blocked",
                "state": "success",
                "detail": "availability, latency, and burn-rate violations detected",
                "evidence": "promotion_blocked",
            },
            {
                "name": "Error budget burn",
                "state": "success",
                "detail": "synthetic candidate exceeded the burn-rate threshold",
                "evidence": "burn_rate_violation_detected",
            },
            {
                "name": "Staged promotion",
                "state": "success",
                "detail": "safe release promoted through build, staging, canary, and production",
                "evidence": "release.staged_promotion.completed",
            },
            {
                "name": "Production approval",
                "state": "success",
                "detail": "synthetic production approval recorded before promotion",
                "evidence": "production_approval_recorded",
            },
            {
                "name": "Promotion history",
                "state": "success",
                "detail": "promotion history hash recorded for auditability",
                "evidence": "promotion_history_hash_recorded",
            },
            {
                "name": "Runtime rollout",
                "state": "success",
                "detail": "private staging runtime evidence is collected through public-safe contracts",
                "evidence": "runtime.rollout.evidence_collected",
            },
            {
                "name": "Loopback boundary",
                "state": "success",
                "detail": "private staging checks stay behind a loopback-only public boundary",
                "evidence": "loopback_boundary_recorded",
            },
            {
                "name": "Private state validation",
                "state": "success",
                "detail": "read-only private infra validation evidence is recorded",
                "evidence": "infra.private_state.validated",
            },
            {
                "name": "No runtime mutation",
                "state": "success",
                "detail": "validation records that no runtime mutation was performed",
                "evidence": "no_runtime_mutation_recorded",
            },
            {
                "name": "Remediation plan",
                "state": "success",
                "detail": "drift remediation is planned with operator review before apply",
                "evidence": "infra.remediation.plan.ready",
            },
            {
                "name": "Rollback attached",
                "state": "success",
                "detail": "remediation plan includes rollback context",
                "evidence": "rollback_attached",
            },
            {
                "name": "Remediation execution",
                "state": "success",
                "detail": "reviewed private staging remediation execution is recorded",
                "evidence": "infra.remediation.execution.completed",
            },
            {
                "name": "Post-remediation validation",
                "state": "success",
                "detail": "postcheck validation is recorded after remediation execution",
                "evidence": "post_remediation_validation_recorded",
            },
            {
                "name": "Post-remediation drift",
                "state": "success",
                "detail": "read-only drift refresh shows clean state after remediation",
                "evidence": "infra.post_remediation_drift.clean",
            },
            {
                "name": "No residual drift",
                "state": "success",
                "detail": "post-remediation refresh records no residual drift",
                "evidence": "no_residual_drift_recorded",
            },
            {
                "name": "Scheduled validation",
                "state": "success",
                "detail": "daily public-safe validation workflow is recorded",
                "evidence": "infra.scheduled_validation.healthy",
            },
            {
                "name": "Missed-run guard",
                "state": "success",
                "detail": "missed scheduled checks require operator review",
                "evidence": "missed_run_guard_recorded",
            },
            {
                "name": "Scheduled alerting",
                "state": "success",
                "detail": "failed or missed scheduled checks produce runbook-backed alert evidence",
                "evidence": "infra.scheduled_validation.alerting.ready",
            },
            {
                "name": "Failure artifact",
                "state": "success",
                "detail": "workflow failures upload a public-safe alert artifact",
                "evidence": "public-scheduled-validation-alert",
            },
        ],
        "engineeringProof": {
            "milestone": "engineering_70",
            "status": "validated",
            "updatedAt": "2026-06-18T10:14:36Z",
            "summary": [
                {
                    "label": "CI/CD",
                    "value": "green",
                    "detail": "smoke, release, SDK, and public export gates",
                    "tone": "green",
                },
                {
                    "label": "Runtime",
                    "value": "observable",
                    "detail": "health, readiness, metrics, logs, and SLO evidence",
                    "tone": "blue",
                },
                {
                    "label": "Recovery",
                    "value": "drilled",
                    "detail": "backup, restore, rollback, and staged promotion",
                    "tone": "violet",
                },
                {
                    "label": "Boundary",
                    "value": "public-safe",
                    "detail": "synthetic data, redacted evidence, no secrets",
                    "tone": "green",
                },
            ],
            "gates": [
                {
                    "name": "Core smoke",
                    "status": "passed",
                    "command": "bash scripts/ci_smoke_public.sh",
                    "evidence": "API, worker, RBAC, outbox, integration, and observability checks",
                },
                {
                    "name": "Public demo API",
                    "status": "passed",
                    "command": "bash scripts/check_public_demo_api.sh",
                    "evidence": "GET /demo/public, OpenAPI, examples, generated clients",
                },
                {
                    "name": "Backup and restore",
                    "status": "passed",
                    "command": "bash scripts/check_public_backup_restore.sh",
                    "evidence": "backup_sha256_recorded, restore_integrity_ok, counts_match",
                },
                {
                    "name": "Release safety",
                    "status": "passed",
                    "command": (
                        "bash scripts/check_public_release_rollback.sh && "
                        "bash scripts/check_public_staged_promotion.sh"
                    ),
                    "evidence": "rollback, canary gate, approval, and promotion history",
                },
                {
                    "name": "GitOps and IaC",
                    "status": "passed",
                    "command": (
                        "bash scripts/check_public_gitops_layout.sh && "
                        "bash scripts/check_public_opentofu_plan.sh"
                    ),
                    "evidence": "Helm, Argo CD layout, OpenTofu plan, drift records",
                },
            ],
            "evidence": [
                {
                    "title": "System review path",
                    "kind": "doc",
                    "path": "docs/public/SYSTEM_REVIEW_PATH.md",
                    "summary": "Compact route through public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index",
                },
                {
                    "title": "Verification quickstart",
                    "kind": "doc",
                    "path": "docs/public/REVIEWER_QUICKSTART.md",
                    "summary": "Timeboxed 5-minute, 15-minute, and 45-minute external verification path",
                },
                {
                    "title": "Milestone contract",
                    "kind": "doc",
                    "path": "docs/public/PLATFORM_MATURITY_70.md",
                    "summary": "Seven evidence groups with executable validation gates",
                },
                {
                    "title": "Sanitized evidence index",
                    "kind": "doc",
                    "path": "docs/public/SANITIZED_EVIDENCE.md",
                    "summary": "Runtime, recovery, release, GitOps, and boundary evidence",
                },
                {
                    "title": "System design",
                    "kind": "doc",
                    "path": "docs/public/SYSTEM_DESIGN.md",
                    "summary": "Core architecture, async boundaries, adapters, and observability",
                },
                {
                    "title": "Generated SDK",
                    "kind": "sdk",
                    "path": "sdk/generated/public-demo/",
                    "summary": "OpenAPI-driven Python, JavaScript, and TypeScript client artifacts",
                },
            ],
        },
        "workflow": {
            "id": "wf-demo-lead-to-student",
            "title": "Lead to enrolled student",
            "owner": "Front desk",
            "currentStage": "student_sync",
            "summary": "Synthetic intake flow that turns a lead into a student record, contract, audit trail, and integration event.",
            "stages": [
                {
                    "key": "lead_created",
                    "label": "Lead captured",
                    "state": "done",
                    "owner": "Website adapter",
                    "evidence": "lead.created",
                },
                {
                    "key": "student_created",
                    "label": "Student record",
                    "state": "done",
                    "owner": "Front desk",
                    "evidence": "student.created",
                },
                {
                    "key": "contract_ready",
                    "label": "Contract prepared",
                    "state": "done",
                    "owner": "Operations",
                    "evidence": "contract.generated",
                },
                {
                    "key": "audit_recorded",
                    "label": "Audit recorded",
                    "state": "done",
                    "owner": "Core API",
                    "evidence": "audit.recorded",
                },
                {
                    "key": "student_sync",
                    "label": "External sync queued",
                    "state": "current",
                    "owner": "Outbox worker",
                    "evidence": "student.sync.requested",
                },
            ],
        },
        "workflowScenarios": [
            {
                "id": "scenario-contract-approval-sync",
                "title": "Contract approval sync",
                "trigger": "business_record.status_changed contract:draft->approved",
                "actionType": "emit_outbox_event",
                "owner": "Operations",
                "status": "processed",
                "detail": "Approved contract emits an outbox event for downstream document and accounting adapters.",
                "outputs": ["audit_event", "outbox_event", "action_run"],
                "evidence": "workflow.contract_approved",
            },
            {
                "id": "scenario-signature-task",
                "title": "Signature task creation",
                "trigger": "business_record.status_changed contract:approved->signature_required",
                "actionType": "create_task_record",
                "owner": "Front desk",
                "status": "ready",
                "detail": "A staff task is created so the contract cannot silently wait for a manual signature step.",
                "outputs": ["audit_event", "task_record", "action_run"],
                "evidence": "workflow.task_record.created",
            },
            {
                "id": "scenario-accounting-export",
                "title": "Accounting export request",
                "trigger": "business_record.status_changed contract:approved->ready_for_billing",
                "actionType": "request_adapter_sync",
                "owner": "Finance",
                "status": "pending",
                "detail": "Billing-ready contracts request an adapter operation with retry, idempotency, and review evidence.",
                "outputs": ["outbox_event", "integration_job", "action_run"],
                "evidence": "workflow.contract_sync.requested",
            },
        ],
        "endToEndScenario": {
            "id": "scenario-approval-notification-adapter-incident",
            "title": "Approval to recovery proof",
            "summary": (
                "Synthetic path from contract approval through notification, adapter export, "
                "dead-letter incident, recovery, and public evidence."
            ),
            "status": "reviewable",
            "currentStep": "incident_resolved",
            "chain": [
                {
                    "step": "approval",
                    "title": "Contract approved",
                    "owner": "Operations",
                    "state": "processed",
                    "source": "workflowScenarios.scenario-contract-approval-sync",
                    "evidence": "workflow.contract_approved",
                },
                {
                    "step": "notification",
                    "title": "Manager notification queued",
                    "owner": "Workflow engine",
                    "state": "ready",
                    "source": "workflowScenarios.scenario-signature-task",
                    "evidence": "notification.manager_signature_task.created",
                },
                {
                    "step": "adapter",
                    "title": "Accounting export requested",
                    "owner": "Integration hub",
                    "state": "retry",
                    "source": "workflowScenarios.scenario-accounting-export",
                    "evidence": "integration.accounting_export.requested",
                },
                {
                    "step": "incident",
                    "title": "Dead-letter incident opened",
                    "owner": "Operator",
                    "state": "acknowledged",
                    "source": "incidentResponse.incidents",
                    "evidence": "integration.incident.status_changed",
                },
                {
                    "step": "recovery",
                    "title": "Retry and postcheck completed",
                    "owner": "Operator",
                    "state": "resolved",
                    "source": "incidentResponse.recoveryActions",
                    "evidence": "postcheck.gates.passed",
                },
                {
                    "step": "proof",
                    "title": "Public evidence linked",
                    "owner": "Release gate",
                    "state": "validated",
                    "source": "engineeringProof.evidence",
                    "evidence": "docs/public/ENGINEERING_PROOF.md",
                },
            ],
            "proof": [
                "workflow.contract_approved",
                "notification.manager_signature_task.created",
                "integration.accounting_export.requested",
                "integration.incident.status_changed",
                "postcheck.gates.passed",
                "docs/public/ENGINEERING_PROOF.md",
            ],
        },
        "timeline": [
            {
                "time": "09:16",
                "actor": "website.adapter",
                "title": "Lead captured",
                "detail": "Synthetic website form normalized into a DriveDesk lead.",
                "event": "lead.created",
            },
            {
                "time": "09:18",
                "actor": "front_desk",
                "title": "Lead converted",
                "detail": "Front desk accepted the lead and opened a student record.",
                "event": "student.created",
            },
            {
                "time": "09:21",
                "actor": "contract.service",
                "title": "Contract generated",
                "detail": "Contract draft attached to the synthetic student workflow.",
                "event": "contract.generated",
            },
            {
                "time": "09:22",
                "actor": "audit",
                "title": "Audit trail written",
                "detail": "Workflow state change recorded for review.",
                "event": "audit.recorded",
            },
            {
                "time": "09:22",
                "actor": "outbox",
                "title": "Sync queued",
                "detail": "Integration event queued for a future external system adapter.",
                "event": "student.sync.requested",
            },
        ],
        "domainEvents": [
            {
                "event": "lead.created",
                "producer": "website.adapter",
                "consumer": "workflow.engine",
                "status": "processed",
            },
            {
                "event": "student.created",
                "producer": "workflow.engine",
                "consumer": "audit.log",
                "status": "processed",
            },
            {
                "event": "contract.generated",
                "producer": "contract.service",
                "consumer": "document.archive",
                "status": "processed",
            },
            {
                "event": "student.sync.requested",
                "producer": "outbox",
                "consumer": "integration.hub",
                "status": "pending",
            },
        ],
    }
