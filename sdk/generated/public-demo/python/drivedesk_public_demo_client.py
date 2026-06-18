#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from typing import Any


PUBLIC_DEMO_PATH = "/demo/public"
OPERATION_ID = "public_demo_demo_public_get"
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
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "recoveryEvidence",
  "alertRouting",
  "incidentResponse",
  "engineeringProof",
  "workflow",
  "workflowScenarios",
  "timeline",
  "domainEvents"
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
    parts = endpoint.strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0] in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return parts[0], parts[1]
    raise ValueError(f"invalid adapter endpoint contract: {endpoint}")


def _adapter_operation_body(scenario: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    phase = scenario.get("phase")
    base = {
        "requestId": request_id,
        "scenarioId": scenario.get("id"),
        "operation": scenario.get("operation"),
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
    if not isinstance(adapter_scenarios, list) or len(adapter_scenarios) < 4:
        raise ValueError("adapterScenarios is missing or too short")

    adapter_scenario_ids = {scenario.get("id") for scenario in adapter_scenarios if isinstance(scenario, dict)}
    required_adapter_scenarios = {
        "adapter-file-import-preview",
        "adapter-file-import-execute",
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
        "retry_scheduled",
        "review_card",
        "manual_retry_endpoint",
    }
    if not required_adapter_outputs.issubset(adapter_outputs):
        raise ValueError(
            f"adapterScenarios does not include required outputs: {sorted(required_adapter_outputs - adapter_outputs)}"
        )

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
    adapter_plan = build_adapter_operation_plan(payload, "adapter-file-import-preview")
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={payload['workflow']['currentStage']}",
        f"adapterPlan={adapter_plan['phase']}",
        f"operation={OPERATION_ID}",
    )


if __name__ == "__main__":
    main()
