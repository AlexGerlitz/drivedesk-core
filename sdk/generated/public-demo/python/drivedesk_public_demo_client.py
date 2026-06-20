#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from typing import Any


PUBLIC_DEMO_PATH = "/demo/public"
CONNECTOR_REPLAY_PATH = "/demo/connector-fixture-replay"
CONNECTOR_CERTIFICATION_PATH = "/demo/connector-certification"
PROVIDER_ONBOARDING_PATH = "/demo/provider-onboarding"
INTEGRATION_REPAIR_PATH = "/demo/integration-repair"
OBSERVABILITY_DASHBOARD_PATH = "/demo/observability-dashboard"
BUSINESS_SCENARIO_REPLAY_PATH = "/demo/business-scenario-replay"
OPERATION_ID = "public_demo_demo_public_get"
CONNECTOR_REPLAY_OPERATION_ID = "connector_fixture_replay_demo_demo_connector_fixture_replay_get"
CONNECTOR_CERTIFICATION_OPERATION_ID = "connector_certification_demo_demo_connector_certification_get"
PROVIDER_ONBOARDING_OPERATION_ID = "provider_onboarding_demo_demo_provider_onboarding_get"
INTEGRATION_REPAIR_OPERATION_ID = "integration_repair_demo_demo_integration_repair_get"
OBSERVABILITY_DASHBOARD_OPERATION_ID = "observability_dashboard_demo_demo_observability_dashboard_get"
BUSINESS_SCENARIO_REPLAY_OPERATION_ID = "business_scenario_replay_demo_demo_business_scenario_replay_get"
REQUIRED_FIELDS = [
  "schemaVersion",
  "generatedAt",
  "dataSource",
  "apiContract",
  "tenant",
  "health",
  "metrics",
  "workQueue",
  "members",
  "auditEvents",
  "outbox",
  "adapters",
  "adapterScenarios",
  "adapterStudio",
  "connectorCertification",
  "providerOnboarding",
  "integrationRuntime",
  "integrationExecution",
  "integrationRepair",
  "observabilityDashboard",
  "notificationDelivery",
  "connectorFixtureReplay",
  "businessIntakePipeline",
  "businessTaskHandoff",
  "businessNotificationChannels",
  "businessContextAssistant",
  "businessActionExecution",
  "businessApprovalGateway",
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "recoveryEvidence",
  "alertRouting",
  "incidentResponse",
  "businessControlTower",
  "businessScenarioReplay",
  "stackReadiness",
  "engineeringProof",
  "workflow",
  "workflowScenarios",
  "endToEndScenario",
  "timeline",
  "domainEvents"
]
CONNECTOR_REPLAY_REQUIRED_FIELDS = [
  "status",
  "command",
  "fixtureFile",
  "evidenceFile",
  "summary",
  "outcomes",
  "boundaries",
  "docs"
]
CONNECTOR_CERTIFICATION_REQUIRED_FIELDS = [
  "status",
  "command",
  "certificationLevel",
  "adapterCount",
  "privateReadyCount",
  "summary",
  "providerProfiles",
  "certificationStages",
  "certificationGates",
  "implementationPath",
  "dataBoundaries",
  "api",
  "docs"
]
PROVIDER_ONBOARDING_REQUIRED_FIELDS = [
  "status",
  "command",
  "onboardingLevel",
  "providerKey",
  "providerName",
  "providerCategory",
  "readinessScore",
  "readinessStatus",
  "summary",
  "providerProfile",
  "onboardingStages",
  "readinessGates",
  "readinessBlockers",
  "privateConnectorHandoff",
  "mappingPreview",
  "preflightChecks",
  "sandboxContract",
  "rolloutPlan",
  "dataBoundaries",
  "api",
  "docs"
]
INTEGRATION_REPAIR_REQUIRED_FIELDS = [
  "status",
  "command",
  "repairLevel",
  "incidentCount",
  "criticalCount",
  "safeActionCount",
  "summary",
  "incidentMatrix",
  "repairRunbooks",
  "impactAnalysis",
  "repairActions",
  "safeExecutionPlan",
  "dataBoundaries",
  "api",
  "docs"
]
OBSERVABILITY_DASHBOARD_REQUIRED_FIELDS = [
  "status",
  "command",
  "dashboardLevel",
  "summary",
  "dashboardGroups",
  "panelCatalog",
  "queryExamples",
  "alertLinks",
  "dataBoundaries",
  "api",
  "docs"
]
BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS = [
  "status",
  "command",
  "summary",
  "scenarios",
  "flow",
  "docs"
]


class DriveDeskPublicDemoClient:
    """Generated OpenAPI client for the public DriveDesk demo endpoint."""

    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_public_demo(self) -> dict[str, Any]:
        payload = self._get_json(PUBLIC_DEMO_PATH)
        validate_public_demo_payload(payload)
        return payload

    def get_connector_fixture_replay(self) -> dict[str, Any]:
        payload = self._get_json(CONNECTOR_REPLAY_PATH)
        validate_connector_fixture_replay_payload(payload)
        return payload

    def get_connector_certification(self) -> dict[str, Any]:
        payload = self._get_json(CONNECTOR_CERTIFICATION_PATH)
        validate_connector_certification_payload(payload)
        return payload

    def get_provider_onboarding(self) -> dict[str, Any]:
        payload = self._get_json(PROVIDER_ONBOARDING_PATH)
        validate_provider_onboarding_payload(payload)
        return payload

    def get_integration_repair(self) -> dict[str, Any]:
        payload = self._get_json(INTEGRATION_REPAIR_PATH)
        validate_integration_repair_payload(payload)
        return payload

    def get_observability_dashboard(self) -> dict[str, Any]:
        payload = self._get_json(OBSERVABILITY_DASHBOARD_PATH)
        validate_observability_dashboard_payload(payload)
        return payload

    def get_business_scenario_replay(self) -> dict[str, Any]:
        payload = self._get_json(BUSINESS_SCENARIO_REPLAY_PATH)
        validate_business_scenario_replay_payload(payload)
        return payload

    def get_adapter_operation_plan(
        self,
        scenario_id: str,
        request_id: str = "demo-request-001",
    ) -> dict[str, Any]:
        payload = self.get_public_demo()
        return build_adapter_operation_plan(payload, scenario_id, request_id=request_id)

    def _get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Accept": "application/json", "User-Agent": "drivedesk-public-demo-sdk/1"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def get_adapter_scenario(payload: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    scenarios = payload.get("adapterScenarios")
    if not isinstance(scenarios, list):
        raise ValueError("adapterScenarios is missing")

    for scenario in scenarios:
        if isinstance(scenario, dict) and scenario.get("id") == scenario_id:
            return scenario

    raise ValueError(f"unknown adapter scenario: {scenario_id}")


def build_adapter_operation_plan(
    payload: dict[str, Any],
    scenario_id: str,
    request_id: str = "demo-request-001",
) -> dict[str, Any]:
    validate_public_demo_payload(payload)
    scenario = get_adapter_scenario(payload, scenario_id)
    method, path = _split_adapter_endpoint(str(scenario.get("endpoint", "")))
    headers: dict[str, str] = {
        "Accept": "application/json",
        "X-DriveDesk-Tenant": str((payload.get("tenant") or {}).get("slug", "demo-academy")),
    }
    if method != "GET":
        headers["Content-Type"] = "application/json"
        headers["Idempotency-Key"] = f"{scenario_id}:{request_id}"

    return {
        "scenarioId": scenario_id,
        "adapter": scenario.get("adapter"),
        "operation": scenario.get("operation"),
        "phase": scenario.get("phase"),
        "executionMode": "contract_only",
        "safeToRunAgainstPublicDemo": False,
        "request": {
            "method": method,
            "path": path,
            "headers": headers,
            "body": _adapter_operation_body(scenario, request_id),
        },
        "expectedResponse": {
            "status": scenario.get("status"),
            "outputs": list(scenario.get("outputs", [])),
            "evidence": scenario.get("evidence"),
            "sideEffects": _adapter_side_effects(scenario),
        },
    }


def _split_adapter_endpoint(endpoint: str) -> tuple[str, str]:
    if endpoint.startswith("worker:"):
        return "WORKER", endpoint
    parts = endpoint.strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0] in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return parts[0], parts[1]
    raise ValueError(f"invalid adapter endpoint contract: {endpoint}")


def _adapter_operation_body(scenario: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    phase = scenario.get("phase")
    operation = scenario.get("operation")
    base = {
        "requestId": request_id,
        "scenarioId": scenario.get("id"),
        "operation": operation,
    }

    if operation == "crm_deal_intake_preview":
        return {
            **base,
            "dryRun": True,
            "provider_key": "crm.bitrix24.mock",
            "source_type": "crm_deal",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "crm-deal-001",
            "provider_payload": {
                "stage": "invoice_sent",
                "amount": 1500,
                "owner_role": "sales",
                "full_name": "Synthetic Customer",
                "phone": "+70000000000",
                "access_token": "never-return-this",
            },
        }

    if operation == "crm_deal_ingest_execute":
        return {
            **base,
            "dryRun": False,
            "batch_id": "bitrix_demo_batch",
            "mapping": {
                "deal_id": "ID",
                "source_state": "STAGE_ID",
                "owner_role": "ASSIGNED_BY_ROLE",
                "amount": "OPPORTUNITY",
            },
            "deals": [
                {
                    "ID": "DEAL-2026-001",
                    "STAGE_ID": "invoice_sent",
                    "ASSIGNED_BY_ROLE": "sales",
                    "OPPORTUNITY": 1500,
                },
            ],
            "confirm": True,
        }

    if phase == "preview":
        return {
            **base,
            "dryRun": True,
            "mappingProfile": "public-demo-v1",
            "sourceRef": "synthetic-file-import",
            "sampleRows": [
                {"externalId": "lead-001", "personRef": "person-demo-001", "courseRef": "course-b"},
            ],
        }

    if phase == "execute":
        return {
            **base,
            "dryRun": False,
            "previewId": "preview-demo-001",
            "confirm": True,
        }

    if phase == "retry":
        return {
            **base,
            "failedJobId": "job-demo-retry-001",
            "retryMode": "same_payload",
            "attempt": 3,
        }

    if phase == "operator_review":
        return None

    raise ValueError(f"unsupported adapter scenario phase: {phase}")


def _adapter_side_effects(scenario: dict[str, Any]) -> list[str]:
    outputs = set(scenario.get("outputs", []))
    side_effects: list[str] = []
    if "mapping_preview" in outputs:
        side_effects.append("validates mapping without creating outbox events")
    if "outbox_event" in outputs:
        side_effects.append("creates outbox event for asynchronous adapter processing")
    if "adapter_job" in outputs:
        side_effects.append("records adapter job status for operator visibility")
    if "retry_scheduled" in outputs:
        side_effects.append("schedules retry with bounded attempt tracking")
    if "review_card" in outputs:
        side_effects.append("creates operator review card for dead-letter handling")
    return side_effects


def validate_connector_fixture_replay_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in CONNECTOR_REPLAY_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing connector fixture replay fields: {', '.join(missing)}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected connector replay status: {payload.get('status')}")

    if payload.get("command") != "bash scripts/check_public_connector_fixture_replay.sh":
        raise ValueError(f"unexpected connector replay command: {payload.get('command')}")

    if payload.get("fixtureFile") != "examples/connector-fixtures/replay-fixtures.sanitized.json":
        raise ValueError(f"unexpected connector replay fixtureFile: {payload.get('fixtureFile')}")

    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) < 6:
        raise ValueError("connector replay outcomes are missing or too short")

    groups = {item.get("group") for item in outcomes if isinstance(item, dict)}
    required_groups = {
        "happy_path_preview",
        "sensitive_payload_redaction",
        "invalid_payload",
        "retryable_provider_failure",
        "dead_letter_provider_failure",
        "reconciliation_mismatch",
    }
    if groups != required_groups:
        raise ValueError(f"connector replay groups mismatch: {sorted(groups)}")

    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 4:
        raise ValueError("connector replay boundaries are missing or too short")

    boundary_names = {item.get("name") for item in boundaries if isinstance(item, dict)}
    required_boundaries = {"raw payload", "credentials", "external calls", "persistence"}
    if not required_boundaries.issubset(boundary_names):
        raise ValueError(
            f"connector replay boundaries missing: {sorted(required_boundaries - boundary_names)}"
        )

    docs = payload.get("docs")
    if not isinstance(docs, list) or len(docs) < 3:
        raise ValueError("connector replay docs are missing or too short")


def validate_connector_certification_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in CONNECTOR_CERTIFICATION_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing connector certification fields: {', '.join(missing)}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected connector certification status: {payload.get('status')}")

    if payload.get("command") != f"GET {CONNECTOR_CERTIFICATION_PATH}":
        raise ValueError(f"unexpected connector certification command: {payload.get('command')}")

    if payload.get("certificationLevel") != "public_contract_certified":
        raise ValueError(
            f"unexpected connector certification level: {payload.get('certificationLevel')}"
        )

    profiles = payload.get("providerProfiles")
    if not isinstance(profiles, list) or len(profiles) < 3:
        raise ValueError("connector certification provider profiles are missing or too short")

    provider_keys = {item.get("adapterKey") for item in profiles if isinstance(item, dict)}
    required_keys = {"crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"}
    if not required_keys.issubset(provider_keys):
        raise ValueError(f"connector certification provider keys missing: {sorted(required_keys - provider_keys)}")

    stages = payload.get("certificationStages")
    if not isinstance(stages, list) or len(stages) < 6:
        raise ValueError("connector certification stages are missing or too short")

    gates = payload.get("certificationGates")
    if not isinstance(gates, list) or len(gates) < 5:
        raise ValueError("connector certification gates are missing or too short")

    if any(item.get("externalMutation") is not False for item in gates if isinstance(item, dict)):
        raise ValueError("connector certification gate must not mutate external providers")

    boundaries = payload.get("dataBoundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 3:
        raise ValueError("connector certification data boundaries are missing or too short")


def validate_provider_onboarding_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in PROVIDER_ONBOARDING_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing provider onboarding fields: {', '.join(missing)}")

    if payload.get("status") != "previewed":
        raise ValueError(f"unexpected provider onboarding status: {payload.get('status')}")

    if payload.get("command") != f"GET {PROVIDER_ONBOARDING_PATH}":
        raise ValueError(f"unexpected provider onboarding command: {payload.get('command')}")

    if payload.get("onboardingLevel") != "sandbox_onboarding_ready":
        raise ValueError(
            f"unexpected provider onboarding level: {payload.get('onboardingLevel')}"
        )

    if payload.get("providerKey") != "crm.bitrix24.mock":
        raise ValueError(f"unexpected provider onboarding key: {payload.get('providerKey')}")

    for key in ("summary", "onboardingStages", "preflightChecks", "rolloutPlan", "dataBoundaries"):
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"provider onboarding {key} is missing or empty")

    sandbox = payload.get("sandboxContract")
    if not isinstance(sandbox, dict) or sandbox.get("providerCallEnabled") is not False:
        raise ValueError("provider onboarding sandbox contract must not call providers")

    if any(
        item.get("externalMutation") is not False
        for item in payload.get("dataBoundaries", [])
        if isinstance(item, dict)
    ):
        raise ValueError("provider onboarding boundaries must not mutate external providers")


def validate_integration_repair_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in INTEGRATION_REPAIR_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing integration repair fields: {', '.join(missing)}")

    if payload.get("status") != "previewed":
        raise ValueError(f"unexpected integration repair status: {payload.get('status')}")

    if payload.get("command") != f"GET {INTEGRATION_REPAIR_PATH}":
        raise ValueError(f"unexpected integration repair command: {payload.get('command')}")

    if payload.get("repairLevel") != "operator_repair_ready":
        raise ValueError(f"unexpected integration repair level: {payload.get('repairLevel')}")

    if payload.get("incidentCount") != 3:
        raise ValueError(f"unexpected integration repair incident count: {payload.get('incidentCount')}")

    if payload.get("criticalCount") != 2:
        raise ValueError(f"unexpected integration repair critical count: {payload.get('criticalCount')}")

    if payload.get("safeActionCount") != 1:
        raise ValueError(f"unexpected integration repair safe action count: {payload.get('safeActionCount')}")

    for key in (
        "summary",
        "incidentMatrix",
        "repairRunbooks",
        "impactAnalysis",
        "repairActions",
        "safeExecutionPlan",
        "dataBoundaries",
    ):
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"integration repair {key} is missing or empty")

    incident_ids = {
        item.get("incidentId")
        for item in payload.get("incidentMatrix", [])
        if isinstance(item, dict)
    }
    required_incidents = {"IR-001", "IR-002", "IR-003"}
    if incident_ids != required_incidents:
        raise ValueError(f"integration repair ids mismatch: {sorted(incident_ids)}")

    runbook_keys = {
        item.get("runbookKey")
        for item in payload.get("repairRunbooks", [])
        if isinstance(item, dict)
    }
    required_runbooks = {
        "integration.retry_backlog",
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
    }
    if runbook_keys != required_runbooks:
        raise ValueError(f"integration repair runbooks mismatch: {sorted(runbook_keys)}")

    safe_actions = [
        item
        for item in payload.get("repairActions", [])
        if isinstance(item, dict) and item.get("safeToAutoRun") is True
    ]
    if len(safe_actions) != 1 or safe_actions[0].get("action") != "run_connection_diagnostics":
        raise ValueError("integration repair must expose exactly one safe diagnostic action")

    for action in payload.get("repairActions", []):
        if not isinstance(action, dict):
            raise ValueError("integration repair action must be an object")
        if action.get("providerCallEnabled") is not False or action.get("externalMutation") is not False:
            raise ValueError("integration repair actions must not call or mutate providers")

    for boundary in payload.get("dataBoundaries", []):
        if not isinstance(boundary, dict):
            raise ValueError("integration repair boundary must be an object")
        if (
            boundary.get("containsPii") is not False
            or boundary.get("rawPayloadIncluded") is not False
            or boundary.get("providerCallEnabled") is not False
            or boundary.get("externalMutation") is not False
        ):
            raise ValueError("integration repair boundaries must stay public-safe")


def validate_observability_dashboard_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in OBSERVABILITY_DASHBOARD_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing observability dashboard fields: {', '.join(missing)}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected observability dashboard status: {payload.get('status')}")

    if payload.get("command") != f"GET {OBSERVABILITY_DASHBOARD_PATH}":
        raise ValueError(
            f"unexpected observability dashboard command: {payload.get('command')}"
        )

    if payload.get("dashboardLevel") != "dashboard_contract_ready":
        raise ValueError(
            f"unexpected observability dashboard level: {payload.get('dashboardLevel')}"
        )

    for key in ("summary", "dashboardGroups", "panelCatalog", "queryExamples", "alertLinks", "dataBoundaries"):
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"observability dashboard {key} is missing or empty")

    group_keys = {item.get("key") for item in payload.get("dashboardGroups", []) if isinstance(item, dict)}
    required_groups = {"api_runtime", "integration_health", "business_workflow", "security_auth"}
    if not required_groups.issubset(group_keys):
        raise ValueError(
            f"observability dashboard groups missing: {sorted(required_groups - group_keys)}"
        )

    panel_keys = {item.get("key") for item in payload.get("panelCatalog", []) if isinstance(item, dict)}
    required_panels = {"request_rate", "latency_p95", "error_ratio", "outbox_backlog", "dead_letters", "structured_logs"}
    if not required_panels.issubset(panel_keys):
        raise ValueError(
            f"observability dashboard panels missing: {sorted(required_panels - panel_keys)}"
        )

    datasources = {item.get("datasource") for item in payload.get("panelCatalog", []) if isinstance(item, dict)}
    if not {"prometheus", "loki"}.issubset(datasources):
        raise ValueError(f"observability dashboard datasources missing: {sorted(datasources)}")

    forbidden_labels = {"email", "user_id", "tenant_id", "token", "phone", "name", "payload", "request_body"}
    for panel in payload.get("panelCatalog", []):
        if not isinstance(panel, dict):
            raise ValueError("observability dashboard panel must be an object")
        labels = set(panel.get("safeLabels", []))
        if not labels.isdisjoint(forbidden_labels):
            raise ValueError(f"unsafe observability dashboard labels: {sorted(labels & forbidden_labels)}")
        if not panel.get("alertLink"):
            raise ValueError(f"observability dashboard panel missing alert link: {panel.get('key')}")

    for boundary in payload.get("dataBoundaries", []):
        if not isinstance(boundary, dict):
            raise ValueError("observability dashboard boundary must be an object")
        if (
            boundary.get("containsPii") is not False
            or boundary.get("rawPayloadIncluded") is not False
            or boundary.get("privateTelemetryIncluded") is not False
        ):
            raise ValueError("observability dashboard boundaries must stay public-safe")


def validate_business_scenario_replay_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing business scenario replay fields: {', '.join(missing)}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected business scenario replay status: {payload.get('status')}")

    if payload.get("command") != "bash scripts/check_public_business_scenario_replay.sh":
        raise ValueError(f"unexpected business scenario replay command: {payload.get('command')}")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 3:
        raise ValueError("business scenario replay scenarios are missing or too short")

    scenario_ids = {item.get("id") for item in scenarios if isinstance(item, dict)}
    required_scenarios = {
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    }
    if scenario_ids != required_scenarios:
        raise ValueError(f"business scenario replay ids mismatch: {sorted(scenario_ids)}")

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("business scenario replay contains non-object scenario")
        if not scenario.get("normalizedFacts"):
            raise ValueError(f"business scenario replay facts missing: {scenario.get('id')}")
        if not scenario.get("recommendedActions"):
            raise ValueError(f"business scenario replay actions missing: {scenario.get('id')}")
        if not any(
            item.get("safeToAutoRun") is False
            for item in scenario.get("automationCandidates", [])
            if isinstance(item, dict)
        ):
            raise ValueError(f"business scenario replay lacks approval boundary: {scenario.get('id')}")

    flow = payload.get("flow")
    if not isinstance(flow, list) or len(flow) < 5:
        raise ValueError("business scenario replay flow is missing or too short")

    docs = payload.get("docs")
    if not isinstance(docs, list) or len(docs) < 4:
        raise ValueError("business scenario replay docs are missing or too short")


def validate_public_demo_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    if payload.get("schemaVersion") != 1:
        raise ValueError(f"unexpected schemaVersion: {payload.get('schemaVersion')}")

    if payload.get("dataSource") != "api.synthetic":
        raise ValueError(f"unexpected dataSource: {payload.get('dataSource')}")

    api_contract = payload.get("apiContract") or {}
    if api_contract.get("path") != PUBLIC_DEMO_PATH:
        raise ValueError(f"unexpected apiContract.path: {api_contract.get('path')}")

    tenant = payload.get("tenant") or {}
    if tenant.get("slug") != "demo-academy":
        raise ValueError(f"unexpected tenant.slug: {tenant.get('slug')}")

    workflow = payload.get("workflow") or {}
    if workflow.get("id") != "wf-demo-lead-to-student":
        raise ValueError(f"unexpected workflow.id: {workflow.get('id')}")

    if workflow.get("currentStage") != "student_sync":
        raise ValueError(f"unexpected workflow.currentStage: {workflow.get('currentStage')}")

    stages = workflow.get("stages")
    if not isinstance(stages, list) or len(stages) < 5:
        raise ValueError("workflow.stages is missing or too short")

    workflow_scenarios = payload.get("workflowScenarios")
    if not isinstance(workflow_scenarios, list) or len(workflow_scenarios) < 3:
        raise ValueError("workflowScenarios is missing or too short")

    scenario_ids = {scenario.get("id") for scenario in workflow_scenarios if isinstance(scenario, dict)}
    required_scenarios = {"scenario-contract-approval-sync", "scenario-signature-task", "scenario-accounting-export"}
    if not required_scenarios.issubset(scenario_ids):
        raise ValueError(f"workflowScenarios does not include required scenarios: {sorted(required_scenarios - scenario_ids)}")

    action_types = {scenario.get("actionType") for scenario in workflow_scenarios if isinstance(scenario, dict)}
    required_actions = {"emit_outbox_event", "create_task_record", "request_adapter_sync"}
    if not required_actions.issubset(action_types):
        raise ValueError(f"workflowScenarios does not include required actions: {sorted(required_actions - action_types)}")

    scenario_outputs = {
        output
        for scenario in workflow_scenarios
        if isinstance(scenario, dict)
        for output in scenario.get("outputs", [])
    }
    required_outputs = {"audit_event", "outbox_event", "task_record", "integration_job", "action_run"}
    if not required_outputs.issubset(scenario_outputs):
        raise ValueError(f"workflowScenarios does not include required outputs: {sorted(required_outputs - scenario_outputs)}")

    adapter_scenarios = payload.get("adapterScenarios")
    if not isinstance(adapter_scenarios, list) or len(adapter_scenarios) < 6:
        raise ValueError("adapterScenarios is missing or too short")

    adapter_scenario_ids = {scenario.get("id") for scenario in adapter_scenarios if isinstance(scenario, dict)}
    required_adapter_scenarios = {
        "adapter-file-import-preview",
        "adapter-file-import-execute",
        "adapter-crm-deal-preview",
        "adapter-crm-deal-ingest",
        "adapter-accounting-export-retry",
        "adapter-dead-letter-review",
    }
    if not required_adapter_scenarios.issubset(adapter_scenario_ids):
        raise ValueError(
            "adapterScenarios does not include required scenarios: "
            f"{sorted(required_adapter_scenarios - adapter_scenario_ids)}"
        )

    adapter_phases = {scenario.get("phase") for scenario in adapter_scenarios if isinstance(scenario, dict)}
    required_adapter_phases = {"preview", "execute", "retry", "operator_review"}
    if not required_adapter_phases.issubset(adapter_phases):
        raise ValueError(f"adapterScenarios does not include required phases: {sorted(required_adapter_phases - adapter_phases)}")

    adapter_outputs = {
        output
        for scenario in adapter_scenarios
        if isinstance(scenario, dict)
        for output in scenario.get("outputs", [])
    }
    required_adapter_outputs = {
        "mapping_preview",
        "outbox_event",
        "adapter_job",
        "safe_payload",
        "normalized_observation",
        "no_provider_call",
        "redaction_evidence",
        "retry_scheduled",
        "review_card",
        "manual_retry_endpoint",
    }
    if not required_adapter_outputs.issubset(adapter_outputs):
        raise ValueError(
            f"adapterScenarios does not include required outputs: {sorted(required_adapter_outputs - adapter_outputs)}"
        )

    adapter_studio = payload.get("adapterStudio") or {}
    for key in ("summary", "flow", "operationPlans", "boundaries", "diagnostics", "docs"):
        value = adapter_studio.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"adapterStudio.{key} is missing or empty")

    adapter_studio_plans = {
        item.get("scenarioId"): item
        for item in adapter_studio.get("operationPlans", [])
        if isinstance(item, dict)
    }
    required_studio_plans = {"adapter-crm-deal-preview", "adapter-crm-deal-ingest"}
    if not required_studio_plans.issubset(adapter_studio_plans):
        raise ValueError(
            "adapterStudio.operationPlans does not include required plans: "
            f"{sorted(required_studio_plans - set(adapter_studio_plans))}"
        )

    if adapter_studio_plans["adapter-crm-deal-preview"].get("executionMode") != "contract_only":
        raise ValueError("adapterStudio CRM preview plan must be contract_only")

    if adapter_studio_plans["adapter-crm-deal-preview"].get("safeToRunAgainstPublicDemo") is not False:
        raise ValueError("adapterStudio CRM preview plan must not be marked safe for live public execution")

    if adapter_studio_plans["adapter-crm-deal-ingest"].get("method") != "WORKER":
        raise ValueError("adapterStudio CRM ingest plan must be worker-backed")

    adapter_studio_boundary_evidence = {
        item.get("evidence")
        for item in adapter_studio.get("boundaries", [])
        if isinstance(item, dict)
    }
    required_boundary_evidence = {"server_secret_store", "private_connector_only", "redaction_evidence"}
    if not required_boundary_evidence.issubset(adapter_studio_boundary_evidence):
        raise ValueError(
            "adapterStudio.boundaries does not include required evidence: "
            f"{sorted(required_boundary_evidence - adapter_studio_boundary_evidence)}"
        )

    connector_replay = payload.get("connectorFixtureReplay")
    if not isinstance(connector_replay, dict):
        raise ValueError("connectorFixtureReplay is missing")
    validate_connector_fixture_replay_payload(connector_replay)

    connector_certification = payload.get("connectorCertification")
    if not isinstance(connector_certification, dict):
        raise ValueError("connectorCertification is missing")
    validate_connector_certification_payload(connector_certification)

    provider_onboarding = payload.get("providerOnboarding")
    if not isinstance(provider_onboarding, dict):
        raise ValueError("providerOnboarding is missing")
    validate_provider_onboarding_payload(provider_onboarding)

    integration_repair = payload.get("integrationRepair")
    if not isinstance(integration_repair, dict):
        raise ValueError("integrationRepair is missing")
    validate_integration_repair_payload(integration_repair)

    observability_dashboard = payload.get("observabilityDashboard")
    if not isinstance(observability_dashboard, dict):
        raise ValueError("observabilityDashboard is missing")
    validate_observability_dashboard_payload(observability_dashboard)

    business_scenario_replay = payload.get("businessScenarioReplay")
    if not isinstance(business_scenario_replay, dict):
        raise ValueError("businessScenarioReplay is missing")
    validate_business_scenario_replay_payload(business_scenario_replay)

    proof = payload.get("engineeringProof") or {}
    if proof.get("milestone") != "engineering_70":
        raise ValueError(f"unexpected engineeringProof.milestone: {proof.get('milestone')}")

    gates = proof.get("gates")
    if not isinstance(gates, list) or len(gates) < 5:
        raise ValueError("engineeringProof.gates is missing or too short")

    alert_routing = payload.get("alertRouting") or {}
    routes = alert_routing.get("routes")
    if not isinstance(routes, list) or len(routes) < 3:
        raise ValueError("alertRouting.routes is missing or too short")

    bindings = alert_routing.get("bindings")
    if not isinstance(bindings, list) or len(bindings) < 5:
        raise ValueError("alertRouting.bindings is missing or too short")

    alert_names = {binding.get("alert") for binding in bindings if isinstance(binding, dict)}
    required_alerts = {"DriveDeskApiTargetDown", "DriveDeskIntegrationDeadLetters", "DriveDeskScheduledValidationMissed"}
    if not required_alerts.issubset(alert_names):
        raise ValueError(f"alertRouting.bindings does not include required alerts: {sorted(required_alerts - alert_names)}")

    incident_response = payload.get("incidentResponse") or {}
    incidents = incident_response.get("incidents")
    if not isinstance(incidents, list) or len(incidents) < 3:
        raise ValueError("incidentResponse.incidents is missing or too short")

    incident_statuses = {incident.get("status") for incident in incidents if isinstance(incident, dict)}
    required_statuses = {"open", "acknowledged", "resolved"}
    if not required_statuses.issubset(incident_statuses):
        raise ValueError(f"incidentResponse.incidents does not include required statuses: {sorted(required_statuses - incident_statuses)}")

    incident_timeline = incident_response.get("timeline")
    if not isinstance(incident_timeline, list) or len(incident_timeline) < 5:
        raise ValueError("incidentResponse.timeline is missing or too short")

    domain_events = payload.get("domainEvents")
    if not isinstance(domain_events, list):
        raise ValueError("domainEvents is missing")

    event_names = {event.get("event") for event in domain_events if isinstance(event, dict)}
    required_events = {"lead.created", "student.created", "contract.generated", "student.sync.requested"}
    if not required_events.issubset(event_names):
        raise ValueError(f"domainEvents does not include required events: {sorted(required_events - event_names)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated DriveDesk public demo client.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    args = parser.parse_args()

    client = DriveDeskPublicDemoClient(args.base_url)
    payload = client.get_public_demo()
    connector_replay = client.get_connector_fixture_replay()
    connector_certification = client.get_connector_certification()
    provider_onboarding = client.get_provider_onboarding()
    integration_repair = client.get_integration_repair()
    observability_dashboard = client.get_observability_dashboard()
    business_scenario_replay = client.get_business_scenario_replay()
    adapter_plan = build_adapter_operation_plan(payload, "adapter-file-import-preview")
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={payload['workflow']['currentStage']}",
        f"adapterPlan={adapter_plan['phase']}",
        f"connectorReplay={connector_replay['status']}",
        f"connectorCertification={connector_certification['certificationLevel']}",
        f"providerOnboarding={provider_onboarding['onboardingLevel']}",
        f"integrationRepair={integration_repair['repairLevel']}",
        f"observabilityDashboard={observability_dashboard['dashboardLevel']}",
        f"businessScenarioReplay={business_scenario_replay['status']}",
        f"operation={OPERATION_ID}",
        f"connectorOperation={CONNECTOR_REPLAY_OPERATION_ID}",
        f"connectorCertificationOperation={CONNECTOR_CERTIFICATION_OPERATION_ID}",
        f"providerOnboardingOperation={PROVIDER_ONBOARDING_OPERATION_ID}",
        f"integrationRepairOperation={INTEGRATION_REPAIR_OPERATION_ID}",
        f"observabilityDashboardOperation={OBSERVABILITY_DASHBOARD_OPERATION_ID}",
        f"businessScenarioOperation={BUSINESS_SCENARIO_REPLAY_OPERATION_ID}",
    )


if __name__ == "__main__":
    main()
