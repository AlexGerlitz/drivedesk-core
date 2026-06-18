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
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "recoveryEvidence",
  "alertRouting",
  "engineeringProof",
  "workflow",
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

    def _get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Accept": "application/json", "User-Agent": "drivedesk-public-demo-sdk/1"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


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
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={payload['workflow']['currentStage']}",
        f"operation={OPERATION_ID}",
    )


if __name__ == "__main__":
    main()
