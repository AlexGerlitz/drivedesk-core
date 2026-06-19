#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PUBLIC_DEMO_PATH = "/demo/public"
PUBLIC_DEMO_METHOD = "get"
CONNECTOR_REPLAY_PATH = "/demo/connector-fixture-replay"
CONNECTOR_REPLAY_METHOD = "get"
CONNECTOR_CERTIFICATION_PATH = "/demo/connector-certification"
CONNECTOR_CERTIFICATION_METHOD = "get"
PROVIDER_ONBOARDING_PATH = "/demo/provider-onboarding"
PROVIDER_ONBOARDING_METHOD = "get"
BUSINESS_INTAKE_PIPELINE_PATH = "/demo/business-intake-pipeline"
BUSINESS_INTAKE_PIPELINE_METHOD = "get"
BUSINESS_TASK_HANDOFF_PATH = "/demo/business-task-handoff"
BUSINESS_TASK_HANDOFF_METHOD = "get"
BUSINESS_NOTIFICATION_CHANNELS_PATH = "/demo/business-notification-channels"
BUSINESS_NOTIFICATION_CHANNELS_METHOD = "get"
BUSINESS_CONTEXT_ASSISTANT_PATH = "/demo/business-context-assistant"
BUSINESS_CONTEXT_ASSISTANT_METHOD = "get"
BUSINESS_ACTION_EXECUTION_PATH = "/demo/business-action-execution"
BUSINESS_ACTION_EXECUTION_METHOD = "get"
BUSINESS_APPROVAL_GATEWAY_PATH = "/demo/business-approval-gateway"
BUSINESS_APPROVAL_GATEWAY_METHOD = "get"
INTEGRATION_RUNTIME_PATH = "/demo/integration-runtime"
INTEGRATION_RUNTIME_METHOD = "get"
INTEGRATION_EXECUTION_PATH = "/demo/integration-execution"
INTEGRATION_EXECUTION_METHOD = "get"
BUSINESS_SCENARIO_REPLAY_PATH = "/demo/business-scenario-replay"
BUSINESS_SCENARIO_REPLAY_METHOD = "get"


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def required_operation(schema: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    paths = schema.get("paths", {})
    operation = paths.get(path, {}).get(method)
    if not isinstance(operation, dict):
        raise SystemExit(f"OpenAPI schema does not contain {method.upper()} {path}")
    return operation


def public_demo_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(schema, PUBLIC_DEMO_PATH, PUBLIC_DEMO_METHOD)


def connector_replay_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(schema, CONNECTOR_REPLAY_PATH, CONNECTOR_REPLAY_METHOD)


def connector_certification_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        CONNECTOR_CERTIFICATION_PATH,
        CONNECTOR_CERTIFICATION_METHOD,
    )


def provider_onboarding_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        PROVIDER_ONBOARDING_PATH,
        PROVIDER_ONBOARDING_METHOD,
    )


def business_intake_pipeline_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_INTAKE_PIPELINE_PATH,
        BUSINESS_INTAKE_PIPELINE_METHOD,
    )


def business_task_handoff_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_TASK_HANDOFF_PATH,
        BUSINESS_TASK_HANDOFF_METHOD,
    )


def business_notification_channels_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_NOTIFICATION_CHANNELS_PATH,
        BUSINESS_NOTIFICATION_CHANNELS_METHOD,
    )


def business_context_assistant_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_CONTEXT_ASSISTANT_PATH,
        BUSINESS_CONTEXT_ASSISTANT_METHOD,
    )


def business_action_execution_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_ACTION_EXECUTION_PATH,
        BUSINESS_ACTION_EXECUTION_METHOD,
    )


def business_approval_gateway_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_APPROVAL_GATEWAY_PATH,
        BUSINESS_APPROVAL_GATEWAY_METHOD,
    )


def integration_runtime_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        INTEGRATION_RUNTIME_PATH,
        INTEGRATION_RUNTIME_METHOD,
    )


def integration_execution_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        INTEGRATION_EXECUTION_PATH,
        INTEGRATION_EXECUTION_METHOD,
    )


def business_scenario_replay_operation(schema: dict[str, Any]) -> dict[str, Any]:
    return required_operation(
        schema,
        BUSINESS_SCENARIO_REPLAY_PATH,
        BUSINESS_SCENARIO_REPLAY_METHOD,
    )


def public_demo_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    public_demo = schemas.get("PublicDemoRead", {})
    required = public_demo.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain PublicDemoRead.required")
    return [str(item) for item in required]


def connector_replay_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    connector_replay = schemas.get("ConnectorFixtureReplayRead", {})
    required = connector_replay.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain ConnectorFixtureReplayRead.required")
    return [str(item) for item in required]


def connector_certification_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    certification = schemas.get("ConnectorCertificationRead", {})
    required = certification.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain ConnectorCertificationRead.required")
    return [str(item) for item in required]


def provider_onboarding_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    onboarding = schemas.get("ProviderOnboardingRead", {})
    required = onboarding.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain ProviderOnboardingRead.required")
    return [str(item) for item in required]


def business_intake_pipeline_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    replay = schemas.get("BusinessIntakePipelineDemoRead", {})
    required = replay.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessIntakePipelineDemoRead.required")
    return [str(item) for item in required]


def business_task_handoff_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    handoff = schemas.get("BusinessTaskHandoffDemoRead", {})
    required = handoff.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessTaskHandoffDemoRead.required")
    return [str(item) for item in required]


def business_notification_channels_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    matrix = schemas.get("BusinessNotificationChannelMatrixDemoRead", {})
    required = matrix.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit(
            "OpenAPI schema does not contain BusinessNotificationChannelMatrixDemoRead.required"
        )
    return [str(item) for item in required]


def business_context_assistant_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    assistant = schemas.get("BusinessContextAssistantDemoRead", {})
    required = assistant.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessContextAssistantDemoRead.required")
    return [str(item) for item in required]


def business_action_execution_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    execution = schemas.get("BusinessActionExecutionDemoRead", {})
    required = execution.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessActionExecutionDemoRead.required")
    return [str(item) for item in required]


def business_approval_gateway_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    gateway = schemas.get("BusinessApprovalGatewayDemoRead", {})
    required = gateway.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessApprovalGatewayDemoRead.required")
    return [str(item) for item in required]


def integration_runtime_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    runtime = schemas.get("IntegrationRuntimeDemoRead", {})
    required = runtime.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain IntegrationRuntimeDemoRead.required")
    return [str(item) for item in required]


def integration_execution_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    execution = schemas.get("IntegrationExecutionDemoRead", {})
    required = execution.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain IntegrationExecutionDemoRead.required")
    return [str(item) for item in required]


def business_scenario_replay_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    replay = schemas.get("BusinessScenarioReplayRead", {})
    required = replay.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain BusinessScenarioReplayRead.required")
    return [str(item) for item in required]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_python_client(
    operation_id: str,
    required_fields: list[str],
    connector_operation_id: str,
    connector_required_fields: list[str],
    connector_certification_operation_id: str,
    connector_certification_required_fields: list[str],
    provider_onboarding_operation_id: str,
    provider_onboarding_required_fields: list[str],
    business_scenario_operation_id: str,
    business_scenario_required_fields: list[str],
) -> str:
    required_json = json.dumps(required_fields, indent=2)
    connector_required_json = json.dumps(connector_required_fields, indent=2)
    connector_certification_required_json = json.dumps(
        connector_certification_required_fields,
        indent=2,
    )
    provider_onboarding_required_json = json.dumps(
        provider_onboarding_required_fields,
        indent=2,
    )
    business_scenario_required_json = json.dumps(business_scenario_required_fields, indent=2)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from typing import Any


PUBLIC_DEMO_PATH = "{PUBLIC_DEMO_PATH}"
CONNECTOR_REPLAY_PATH = "{CONNECTOR_REPLAY_PATH}"
CONNECTOR_CERTIFICATION_PATH = "{CONNECTOR_CERTIFICATION_PATH}"
PROVIDER_ONBOARDING_PATH = "{PROVIDER_ONBOARDING_PATH}"
BUSINESS_SCENARIO_REPLAY_PATH = "{BUSINESS_SCENARIO_REPLAY_PATH}"
OPERATION_ID = "{operation_id}"
CONNECTOR_REPLAY_OPERATION_ID = "{connector_operation_id}"
CONNECTOR_CERTIFICATION_OPERATION_ID = "{connector_certification_operation_id}"
PROVIDER_ONBOARDING_OPERATION_ID = "{provider_onboarding_operation_id}"
BUSINESS_SCENARIO_REPLAY_OPERATION_ID = "{business_scenario_operation_id}"
REQUIRED_FIELDS = {required_json}
CONNECTOR_REPLAY_REQUIRED_FIELDS = {connector_required_json}
CONNECTOR_CERTIFICATION_REQUIRED_FIELDS = {connector_certification_required_json}
PROVIDER_ONBOARDING_REQUIRED_FIELDS = {provider_onboarding_required_json}
BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS = {business_scenario_required_json}


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
            f"{{self.base_url}}{{path}}",
            headers={{"Accept": "application/json", "User-Agent": "drivedesk-public-demo-sdk/1"}},
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

    raise ValueError(f"unknown adapter scenario: {{scenario_id}}")


def build_adapter_operation_plan(
    payload: dict[str, Any],
    scenario_id: str,
    request_id: str = "demo-request-001",
) -> dict[str, Any]:
    validate_public_demo_payload(payload)
    scenario = get_adapter_scenario(payload, scenario_id)
    method, path = _split_adapter_endpoint(str(scenario.get("endpoint", "")))
    headers: dict[str, str] = {{
        "Accept": "application/json",
        "X-DriveDesk-Tenant": str((payload.get("tenant") or {{}}).get("slug", "demo-academy")),
    }}
    if method != "GET":
        headers["Content-Type"] = "application/json"
        headers["Idempotency-Key"] = f"{{scenario_id}}:{{request_id}}"

    return {{
        "scenarioId": scenario_id,
        "adapter": scenario.get("adapter"),
        "operation": scenario.get("operation"),
        "phase": scenario.get("phase"),
        "executionMode": "contract_only",
        "safeToRunAgainstPublicDemo": False,
        "request": {{
            "method": method,
            "path": path,
            "headers": headers,
            "body": _adapter_operation_body(scenario, request_id),
        }},
        "expectedResponse": {{
            "status": scenario.get("status"),
            "outputs": list(scenario.get("outputs", [])),
            "evidence": scenario.get("evidence"),
            "sideEffects": _adapter_side_effects(scenario),
        }},
    }}


def _split_adapter_endpoint(endpoint: str) -> tuple[str, str]:
    if endpoint.startswith("worker:"):
        return "WORKER", endpoint
    parts = endpoint.strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0] in {{"GET", "POST", "PUT", "PATCH", "DELETE"}}:
        return parts[0], parts[1]
    raise ValueError(f"invalid adapter endpoint contract: {{endpoint}}")


def _adapter_operation_body(scenario: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    phase = scenario.get("phase")
    operation = scenario.get("operation")
    base = {{
        "requestId": request_id,
        "scenarioId": scenario.get("id"),
        "operation": operation,
    }}

    if operation == "crm_deal_intake_preview":
        return {{
            **base,
            "dryRun": True,
            "provider_key": "crm.bitrix24.mock",
            "source_type": "crm_deal",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "crm-deal-001",
            "provider_payload": {{
                "stage": "invoice_sent",
                "amount": 1500,
                "owner_role": "sales",
                "full_name": "Synthetic Customer",
                "phone": "+70000000000",
                "access_token": "never-return-this",
            }},
        }}

    if operation == "crm_deal_ingest_execute":
        return {{
            **base,
            "dryRun": False,
            "batch_id": "bitrix_demo_batch",
            "mapping": {{
                "deal_id": "ID",
                "source_state": "STAGE_ID",
                "owner_role": "ASSIGNED_BY_ROLE",
                "amount": "OPPORTUNITY",
            }},
            "deals": [
                {{
                    "ID": "DEAL-2026-001",
                    "STAGE_ID": "invoice_sent",
                    "ASSIGNED_BY_ROLE": "sales",
                    "OPPORTUNITY": 1500,
                }},
            ],
            "confirm": True,
        }}

    if phase == "preview":
        return {{
            **base,
            "dryRun": True,
            "mappingProfile": "public-demo-v1",
            "sourceRef": "synthetic-file-import",
            "sampleRows": [
                {{"externalId": "lead-001", "personRef": "person-demo-001", "courseRef": "course-b"}},
            ],
        }}

    if phase == "execute":
        return {{
            **base,
            "dryRun": False,
            "previewId": "preview-demo-001",
            "confirm": True,
        }}

    if phase == "retry":
        return {{
            **base,
            "failedJobId": "job-demo-retry-001",
            "retryMode": "same_payload",
            "attempt": 3,
        }}

    if phase == "operator_review":
        return None

    raise ValueError(f"unsupported adapter scenario phase: {{phase}}")


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
        raise ValueError(f"missing connector fixture replay fields: {{', '.join(missing)}}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected connector replay status: {{payload.get('status')}}")

    if payload.get("command") != "bash scripts/check_public_connector_fixture_replay.sh":
        raise ValueError(f"unexpected connector replay command: {{payload.get('command')}}")

    if payload.get("fixtureFile") != "examples/connector-fixtures/replay-fixtures.sanitized.json":
        raise ValueError(f"unexpected connector replay fixtureFile: {{payload.get('fixtureFile')}}")

    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) < 6:
        raise ValueError("connector replay outcomes are missing or too short")

    groups = {{item.get("group") for item in outcomes if isinstance(item, dict)}}
    required_groups = {{
        "happy_path_preview",
        "sensitive_payload_redaction",
        "invalid_payload",
        "retryable_provider_failure",
        "dead_letter_provider_failure",
        "reconciliation_mismatch",
    }}
    if groups != required_groups:
        raise ValueError(f"connector replay groups mismatch: {{sorted(groups)}}")

    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 4:
        raise ValueError("connector replay boundaries are missing or too short")

    boundary_names = {{item.get("name") for item in boundaries if isinstance(item, dict)}}
    required_boundaries = {{"raw payload", "credentials", "external calls", "persistence"}}
    if not required_boundaries.issubset(boundary_names):
        raise ValueError(
            f"connector replay boundaries missing: {{sorted(required_boundaries - boundary_names)}}"
        )

    docs = payload.get("docs")
    if not isinstance(docs, list) or len(docs) < 3:
        raise ValueError("connector replay docs are missing or too short")


def validate_connector_certification_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in CONNECTOR_CERTIFICATION_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing connector certification fields: {{', '.join(missing)}}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected connector certification status: {{payload.get('status')}}")

    if payload.get("command") != f"GET {{CONNECTOR_CERTIFICATION_PATH}}":
        raise ValueError(f"unexpected connector certification command: {{payload.get('command')}}")

    if payload.get("certificationLevel") != "public_contract_certified":
        raise ValueError(
            f"unexpected connector certification level: {{payload.get('certificationLevel')}}"
        )

    profiles = payload.get("providerProfiles")
    if not isinstance(profiles, list) or len(profiles) < 3:
        raise ValueError("connector certification provider profiles are missing or too short")

    provider_keys = {{item.get("adapterKey") for item in profiles if isinstance(item, dict)}}
    required_keys = {{"crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"}}
    if not required_keys.issubset(provider_keys):
        raise ValueError(f"connector certification provider keys missing: {{sorted(required_keys - provider_keys)}}")

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
        raise ValueError(f"missing provider onboarding fields: {{', '.join(missing)}}")

    if payload.get("status") != "previewed":
        raise ValueError(f"unexpected provider onboarding status: {{payload.get('status')}}")

    if payload.get("command") != f"GET {{PROVIDER_ONBOARDING_PATH}}":
        raise ValueError(f"unexpected provider onboarding command: {{payload.get('command')}}")

    if payload.get("onboardingLevel") != "sandbox_onboarding_ready":
        raise ValueError(
            f"unexpected provider onboarding level: {{payload.get('onboardingLevel')}}"
        )

    if payload.get("providerKey") != "crm.bitrix24.mock":
        raise ValueError(f"unexpected provider onboarding key: {{payload.get('providerKey')}}")

    for key in ("summary", "onboardingStages", "preflightChecks", "rolloutPlan", "dataBoundaries"):
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"provider onboarding {{key}} is missing or empty")

    sandbox = payload.get("sandboxContract")
    if not isinstance(sandbox, dict) or sandbox.get("providerCallEnabled") is not False:
        raise ValueError("provider onboarding sandbox contract must not call providers")

    if any(
        item.get("externalMutation") is not False
        for item in payload.get("dataBoundaries", [])
        if isinstance(item, dict)
    ):
        raise ValueError("provider onboarding boundaries must not mutate external providers")


def validate_business_scenario_replay_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing business scenario replay fields: {{', '.join(missing)}}")

    if payload.get("status") != "validated":
        raise ValueError(f"unexpected business scenario replay status: {{payload.get('status')}}")

    if payload.get("command") != "bash scripts/check_public_business_scenario_replay.sh":
        raise ValueError(f"unexpected business scenario replay command: {{payload.get('command')}}")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 3:
        raise ValueError("business scenario replay scenarios are missing or too short")

    scenario_ids = {{item.get("id") for item in scenarios if isinstance(item, dict)}}
    required_scenarios = {{
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    }}
    if scenario_ids != required_scenarios:
        raise ValueError(f"business scenario replay ids mismatch: {{sorted(scenario_ids)}}")

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("business scenario replay contains non-object scenario")
        if not scenario.get("normalizedFacts"):
            raise ValueError(f"business scenario replay facts missing: {{scenario.get('id')}}")
        if not scenario.get("recommendedActions"):
            raise ValueError(f"business scenario replay actions missing: {{scenario.get('id')}}")
        if not any(
            item.get("safeToAutoRun") is False
            for item in scenario.get("automationCandidates", [])
            if isinstance(item, dict)
        ):
            raise ValueError(f"business scenario replay lacks approval boundary: {{scenario.get('id')}}")

    flow = payload.get("flow")
    if not isinstance(flow, list) or len(flow) < 5:
        raise ValueError("business scenario replay flow is missing or too short")

    docs = payload.get("docs")
    if not isinstance(docs, list) or len(docs) < 4:
        raise ValueError("business scenario replay docs are missing or too short")


def validate_public_demo_payload(payload: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing required fields: {{', '.join(missing)}}")

    if payload.get("schemaVersion") != 1:
        raise ValueError(f"unexpected schemaVersion: {{payload.get('schemaVersion')}}")

    if payload.get("dataSource") != "api.synthetic":
        raise ValueError(f"unexpected dataSource: {{payload.get('dataSource')}}")

    api_contract = payload.get("apiContract") or {{}}
    if api_contract.get("path") != PUBLIC_DEMO_PATH:
        raise ValueError(f"unexpected apiContract.path: {{api_contract.get('path')}}")

    tenant = payload.get("tenant") or {{}}
    if tenant.get("slug") != "demo-academy":
        raise ValueError(f"unexpected tenant.slug: {{tenant.get('slug')}}")

    workflow = payload.get("workflow") or {{}}
    if workflow.get("id") != "wf-demo-lead-to-student":
        raise ValueError(f"unexpected workflow.id: {{workflow.get('id')}}")

    if workflow.get("currentStage") != "student_sync":
        raise ValueError(f"unexpected workflow.currentStage: {{workflow.get('currentStage')}}")

    stages = workflow.get("stages")
    if not isinstance(stages, list) or len(stages) < 5:
        raise ValueError("workflow.stages is missing or too short")

    workflow_scenarios = payload.get("workflowScenarios")
    if not isinstance(workflow_scenarios, list) or len(workflow_scenarios) < 3:
        raise ValueError("workflowScenarios is missing or too short")

    scenario_ids = {{scenario.get("id") for scenario in workflow_scenarios if isinstance(scenario, dict)}}
    required_scenarios = {{"scenario-contract-approval-sync", "scenario-signature-task", "scenario-accounting-export"}}
    if not required_scenarios.issubset(scenario_ids):
        raise ValueError(f"workflowScenarios does not include required scenarios: {{sorted(required_scenarios - scenario_ids)}}")

    action_types = {{scenario.get("actionType") for scenario in workflow_scenarios if isinstance(scenario, dict)}}
    required_actions = {{"emit_outbox_event", "create_task_record", "request_adapter_sync"}}
    if not required_actions.issubset(action_types):
        raise ValueError(f"workflowScenarios does not include required actions: {{sorted(required_actions - action_types)}}")

    scenario_outputs = {{
        output
        for scenario in workflow_scenarios
        if isinstance(scenario, dict)
        for output in scenario.get("outputs", [])
    }}
    required_outputs = {{"audit_event", "outbox_event", "task_record", "integration_job", "action_run"}}
    if not required_outputs.issubset(scenario_outputs):
        raise ValueError(f"workflowScenarios does not include required outputs: {{sorted(required_outputs - scenario_outputs)}}")

    adapter_scenarios = payload.get("adapterScenarios")
    if not isinstance(adapter_scenarios, list) or len(adapter_scenarios) < 6:
        raise ValueError("adapterScenarios is missing or too short")

    adapter_scenario_ids = {{scenario.get("id") for scenario in adapter_scenarios if isinstance(scenario, dict)}}
    required_adapter_scenarios = {{
        "adapter-file-import-preview",
        "adapter-file-import-execute",
        "adapter-crm-deal-preview",
        "adapter-crm-deal-ingest",
        "adapter-accounting-export-retry",
        "adapter-dead-letter-review",
    }}
    if not required_adapter_scenarios.issubset(adapter_scenario_ids):
        raise ValueError(
            "adapterScenarios does not include required scenarios: "
            f"{{sorted(required_adapter_scenarios - adapter_scenario_ids)}}"
        )

    adapter_phases = {{scenario.get("phase") for scenario in adapter_scenarios if isinstance(scenario, dict)}}
    required_adapter_phases = {{"preview", "execute", "retry", "operator_review"}}
    if not required_adapter_phases.issubset(adapter_phases):
        raise ValueError(f"adapterScenarios does not include required phases: {{sorted(required_adapter_phases - adapter_phases)}}")

    adapter_outputs = {{
        output
        for scenario in adapter_scenarios
        if isinstance(scenario, dict)
        for output in scenario.get("outputs", [])
    }}
    required_adapter_outputs = {{
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
    }}
    if not required_adapter_outputs.issubset(adapter_outputs):
        raise ValueError(
            f"adapterScenarios does not include required outputs: {{sorted(required_adapter_outputs - adapter_outputs)}}"
        )

    adapter_studio = payload.get("adapterStudio") or {{}}
    for key in ("summary", "flow", "operationPlans", "boundaries", "diagnostics", "docs"):
        value = adapter_studio.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"adapterStudio.{{key}} is missing or empty")

    adapter_studio_plans = {{
        item.get("scenarioId"): item
        for item in adapter_studio.get("operationPlans", [])
        if isinstance(item, dict)
    }}
    required_studio_plans = {{"adapter-crm-deal-preview", "adapter-crm-deal-ingest"}}
    if not required_studio_plans.issubset(adapter_studio_plans):
        raise ValueError(
            "adapterStudio.operationPlans does not include required plans: "
            f"{{sorted(required_studio_plans - set(adapter_studio_plans))}}"
        )

    if adapter_studio_plans["adapter-crm-deal-preview"].get("executionMode") != "contract_only":
        raise ValueError("adapterStudio CRM preview plan must be contract_only")

    if adapter_studio_plans["adapter-crm-deal-preview"].get("safeToRunAgainstPublicDemo") is not False:
        raise ValueError("adapterStudio CRM preview plan must not be marked safe for live public execution")

    if adapter_studio_plans["adapter-crm-deal-ingest"].get("method") != "WORKER":
        raise ValueError("adapterStudio CRM ingest plan must be worker-backed")

    adapter_studio_boundary_evidence = {{
        item.get("evidence")
        for item in adapter_studio.get("boundaries", [])
        if isinstance(item, dict)
    }}
    required_boundary_evidence = {{"server_secret_store", "private_connector_only", "redaction_evidence"}}
    if not required_boundary_evidence.issubset(adapter_studio_boundary_evidence):
        raise ValueError(
            "adapterStudio.boundaries does not include required evidence: "
            f"{{sorted(required_boundary_evidence - adapter_studio_boundary_evidence)}}"
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

    business_scenario_replay = payload.get("businessScenarioReplay")
    if not isinstance(business_scenario_replay, dict):
        raise ValueError("businessScenarioReplay is missing")
    validate_business_scenario_replay_payload(business_scenario_replay)

    proof = payload.get("engineeringProof") or {{}}
    if proof.get("milestone") != "engineering_70":
        raise ValueError(f"unexpected engineeringProof.milestone: {{proof.get('milestone')}}")

    gates = proof.get("gates")
    if not isinstance(gates, list) or len(gates) < 5:
        raise ValueError("engineeringProof.gates is missing or too short")

    alert_routing = payload.get("alertRouting") or {{}}
    routes = alert_routing.get("routes")
    if not isinstance(routes, list) or len(routes) < 3:
        raise ValueError("alertRouting.routes is missing or too short")

    bindings = alert_routing.get("bindings")
    if not isinstance(bindings, list) or len(bindings) < 5:
        raise ValueError("alertRouting.bindings is missing or too short")

    alert_names = {{binding.get("alert") for binding in bindings if isinstance(binding, dict)}}
    required_alerts = {{"DriveDeskApiTargetDown", "DriveDeskIntegrationDeadLetters", "DriveDeskScheduledValidationMissed"}}
    if not required_alerts.issubset(alert_names):
        raise ValueError(f"alertRouting.bindings does not include required alerts: {{sorted(required_alerts - alert_names)}}")

    incident_response = payload.get("incidentResponse") or {{}}
    incidents = incident_response.get("incidents")
    if not isinstance(incidents, list) or len(incidents) < 3:
        raise ValueError("incidentResponse.incidents is missing or too short")

    incident_statuses = {{incident.get("status") for incident in incidents if isinstance(incident, dict)}}
    required_statuses = {{"open", "acknowledged", "resolved"}}
    if not required_statuses.issubset(incident_statuses):
        raise ValueError(f"incidentResponse.incidents does not include required statuses: {{sorted(required_statuses - incident_statuses)}}")

    incident_timeline = incident_response.get("timeline")
    if not isinstance(incident_timeline, list) or len(incident_timeline) < 5:
        raise ValueError("incidentResponse.timeline is missing or too short")

    domain_events = payload.get("domainEvents")
    if not isinstance(domain_events, list):
        raise ValueError("domainEvents is missing")

    event_names = {{event.get("event") for event in domain_events if isinstance(event, dict)}}
    required_events = {{"lead.created", "student.created", "contract.generated", "student.sync.requested"}}
    if not required_events.issubset(event_names):
        raise ValueError(f"domainEvents does not include required events: {{sorted(required_events - event_names)}}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated DriveDesk public demo client.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    args = parser.parse_args()

    client = DriveDeskPublicDemoClient(args.base_url)
    payload = client.get_public_demo()
    connector_replay = client.get_connector_fixture_replay()
    connector_certification = client.get_connector_certification()
    provider_onboarding = client.get_provider_onboarding()
    business_scenario_replay = client.get_business_scenario_replay()
    adapter_plan = build_adapter_operation_plan(payload, "adapter-file-import-preview")
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={{payload['workflow']['currentStage']}}",
        f"adapterPlan={{adapter_plan['phase']}}",
        f"connectorReplay={{connector_replay['status']}}",
        f"connectorCertification={{connector_certification['certificationLevel']}}",
        f"providerOnboarding={{provider_onboarding['onboardingLevel']}}",
        f"businessScenarioReplay={{business_scenario_replay['status']}}",
        f"operation={{OPERATION_ID}}",
        f"connectorOperation={{CONNECTOR_REPLAY_OPERATION_ID}}",
        f"connectorCertificationOperation={{CONNECTOR_CERTIFICATION_OPERATION_ID}}",
        f"providerOnboardingOperation={{PROVIDER_ONBOARDING_OPERATION_ID}}",
        f"businessScenarioOperation={{BUSINESS_SCENARIO_REPLAY_OPERATION_ID}}",
    )


if __name__ == "__main__":
    main()
'''


def render_javascript_client(
    operation_id: str,
    required_fields: list[str],
    connector_operation_id: str,
    connector_required_fields: list[str],
    connector_certification_operation_id: str,
    connector_certification_required_fields: list[str],
    provider_onboarding_operation_id: str,
    provider_onboarding_required_fields: list[str],
    business_scenario_operation_id: str,
    business_scenario_required_fields: list[str],
) -> str:
    required_json = json.dumps(required_fields, indent=2)
    connector_required_json = json.dumps(connector_required_fields, indent=2)
    connector_certification_required_json = json.dumps(
        connector_certification_required_fields,
        indent=2,
    )
    provider_onboarding_required_json = json.dumps(
        provider_onboarding_required_fields,
        indent=2,
    )
    business_scenario_required_json = json.dumps(business_scenario_required_fields, indent=2)
    return f'''#!/usr/bin/env node
import {{ pathToFileURL }} from "node:url";

export const PUBLIC_DEMO_PATH = "{PUBLIC_DEMO_PATH}";
export const CONNECTOR_REPLAY_PATH = "{CONNECTOR_REPLAY_PATH}";
export const CONNECTOR_CERTIFICATION_PATH = "{CONNECTOR_CERTIFICATION_PATH}";
export const PROVIDER_ONBOARDING_PATH = "{PROVIDER_ONBOARDING_PATH}";
export const BUSINESS_SCENARIO_REPLAY_PATH = "{BUSINESS_SCENARIO_REPLAY_PATH}";
export const OPERATION_ID = "{operation_id}";
export const CONNECTOR_REPLAY_OPERATION_ID = "{connector_operation_id}";
export const CONNECTOR_CERTIFICATION_OPERATION_ID = "{connector_certification_operation_id}";
export const PROVIDER_ONBOARDING_OPERATION_ID = "{provider_onboarding_operation_id}";
export const BUSINESS_SCENARIO_REPLAY_OPERATION_ID = "{business_scenario_operation_id}";
export const REQUIRED_FIELDS = {required_json};
export const CONNECTOR_REPLAY_REQUIRED_FIELDS = {connector_required_json};
export const CONNECTOR_CERTIFICATION_REQUIRED_FIELDS = {connector_certification_required_json};
export const PROVIDER_ONBOARDING_REQUIRED_FIELDS = {provider_onboarding_required_json};
export const BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS = {business_scenario_required_json};

export class DriveDeskPublicDemoClient {{
  constructor(baseUrl = "http://localhost:8080", options = {{}}) {{
    this.baseUrl = baseUrl.replace(/\\/$/, "");
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    if (!this.fetchImpl) {{
      throw new Error("fetch is not available in this JavaScript runtime");
    }}
  }}

  async getPublicDemo() {{
    const response = await this.fetchImpl(`${{this.baseUrl}}${{PUBLIC_DEMO_PATH}}`, {{
      headers: {{
        Accept: "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`GET ${{PUBLIC_DEMO_PATH}} failed: ${{response.status}}`);
    }}

    const payload = await response.json();
    validatePublicDemoPayload(payload);
    return payload;
  }}

  async getConnectorFixtureReplay() {{
    const response = await this.fetchImpl(`${{this.baseUrl}}${{CONNECTOR_REPLAY_PATH}}`, {{
      headers: {{
        Accept: "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`GET ${{CONNECTOR_REPLAY_PATH}} failed: ${{response.status}}`);
    }}

    const payload = await response.json();
    validateConnectorFixtureReplayPayload(payload);
    return payload;
  }}

  async getConnectorCertification() {{
    const response = await this.fetchImpl(`${{this.baseUrl}}${{CONNECTOR_CERTIFICATION_PATH}}`, {{
      headers: {{
        Accept: "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`GET ${{CONNECTOR_CERTIFICATION_PATH}} failed: ${{response.status}}`);
    }}

    const payload = await response.json();
    validateConnectorCertificationPayload(payload);
    return payload;
  }}

  async getProviderOnboarding() {{
    const response = await this.fetchImpl(`${{this.baseUrl}}${{PROVIDER_ONBOARDING_PATH}}`, {{
      headers: {{
        Accept: "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`GET ${{PROVIDER_ONBOARDING_PATH}} failed: ${{response.status}}`);
    }}

    const payload = await response.json();
    validateProviderOnboardingPayload(payload);
    return payload;
  }}

  async getBusinessScenarioReplay() {{
    const response = await this.fetchImpl(`${{this.baseUrl}}${{BUSINESS_SCENARIO_REPLAY_PATH}}`, {{
      headers: {{
        Accept: "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`GET ${{BUSINESS_SCENARIO_REPLAY_PATH}} failed: ${{response.status}}`);
    }}

    const payload = await response.json();
    validateBusinessScenarioReplayPayload(payload);
    return payload;
  }}

  async getAdapterOperationPlan(scenarioId, options = {{}}) {{
    const payload = await this.getPublicDemo();
    return buildAdapterOperationPlan(payload, scenarioId, options);
  }}
}}

export function getAdapterScenario(payload, scenarioId) {{
  if (!Array.isArray(payload.adapterScenarios)) {{
    throw new Error("adapterScenarios is missing");
  }}

  const scenario = payload.adapterScenarios.find((item) => item?.id === scenarioId);
  if (!scenario) {{
    throw new Error(`unknown adapter scenario: ${{scenarioId}}`);
  }}

  return scenario;
}}

export function buildAdapterOperationPlan(payload, scenarioId, options = {{}}) {{
  validatePublicDemoPayload(payload);
  const scenario = getAdapterScenario(payload, scenarioId);
  const [method, path] = splitAdapterEndpoint(scenario.endpoint);
  const requestId = options.requestId || "demo-request-001";
  const headers = {{
    Accept: "application/json",
    "X-DriveDesk-Tenant": payload.tenant?.slug || "demo-academy",
  }};

  if (method !== "GET") {{
    headers["Content-Type"] = "application/json";
    headers["Idempotency-Key"] = `${{scenarioId}}:${{requestId}}`;
  }}

  return {{
    scenarioId,
    adapter: scenario.adapter,
    operation: scenario.operation,
    phase: scenario.phase,
    executionMode: "contract_only",
    safeToRunAgainstPublicDemo: false,
    request: {{
      method,
      path,
      headers,
      body: adapterOperationBody(scenario, requestId),
    }},
    expectedResponse: {{
      status: scenario.status,
      outputs: [...(scenario.outputs || [])],
      evidence: scenario.evidence,
      sideEffects: adapterSideEffects(scenario),
    }},
  }};
}}

function splitAdapterEndpoint(endpoint) {{
  if (String(endpoint || "").startsWith("worker:")) {{
    return ["WORKER", endpoint];
  }}
  const match = /^(GET|POST|PUT|PATCH|DELETE)\\s+(.+)$/.exec(String(endpoint || "").trim());
  if (!match) {{
    throw new Error(`invalid adapter endpoint contract: ${{endpoint}}`);
  }}
  return [match[1], match[2]];
}}

function adapterOperationBody(scenario, requestId) {{
  const base = {{
    requestId,
    scenarioId: scenario.id,
    operation: scenario.operation,
  }};

  if (scenario.operation === "crm_deal_intake_preview") {{
    return {{
      ...base,
      dryRun: true,
      provider_key: "crm.bitrix24.mock",
      source_type: "crm_deal",
      subject_type: "deal",
      subject_id: "DEAL-2026-001",
      external_ref: "crm-deal-001",
      provider_payload: {{
        stage: "invoice_sent",
        amount: 1500,
        owner_role: "sales",
        full_name: "Synthetic Customer",
        phone: "+70000000000",
        access_token: "never-return-this",
      }},
    }};
  }}

  if (scenario.operation === "crm_deal_ingest_execute") {{
    return {{
      ...base,
      dryRun: false,
      batch_id: "bitrix_demo_batch",
      mapping: {{
        deal_id: "ID",
        source_state: "STAGE_ID",
        owner_role: "ASSIGNED_BY_ROLE",
        amount: "OPPORTUNITY",
      }},
      deals: [
        {{
          ID: "DEAL-2026-001",
          STAGE_ID: "invoice_sent",
          ASSIGNED_BY_ROLE: "sales",
          OPPORTUNITY: 1500,
        }},
      ],
      confirm: true,
    }};
  }}

  if (scenario.phase === "preview") {{
    return {{
      ...base,
      dryRun: true,
      mappingProfile: "public-demo-v1",
      sourceRef: "synthetic-file-import",
      sampleRows: [
        {{ externalId: "lead-001", personRef: "person-demo-001", courseRef: "course-b" }},
      ],
    }};
  }}

  if (scenario.phase === "execute") {{
    return {{
      ...base,
      dryRun: false,
      previewId: "preview-demo-001",
      confirm: true,
    }};
  }}

  if (scenario.phase === "retry") {{
    return {{
      ...base,
      failedJobId: "job-demo-retry-001",
      retryMode: "same_payload",
      attempt: 3,
    }};
  }}

  if (scenario.phase === "operator_review") {{
    return null;
  }}

  throw new Error(`unsupported adapter scenario phase: ${{scenario.phase}}`);
}}

function adapterSideEffects(scenario) {{
  const outputs = new Set(scenario.outputs || []);
  const sideEffects = [];
  if (outputs.has("mapping_preview")) {{
    sideEffects.push("validates mapping without creating outbox events");
  }}
  if (outputs.has("outbox_event")) {{
    sideEffects.push("creates outbox event for asynchronous adapter processing");
  }}
  if (outputs.has("adapter_job")) {{
    sideEffects.push("records adapter job status for operator visibility");
  }}
  if (outputs.has("retry_scheduled")) {{
    sideEffects.push("schedules retry with bounded attempt tracking");
  }}
  if (outputs.has("review_card")) {{
    sideEffects.push("creates operator review card for dead-letter handling");
  }}
  return sideEffects;
}}

export function validateConnectorFixtureReplayPayload(payload) {{
  const missing = CONNECTOR_REPLAY_REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {{
    throw new Error(`missing connector fixture replay fields: ${{missing.join(", ")}}`);
  }}

  if (payload.status !== "validated") {{
    throw new Error(`unexpected connector replay status: ${{payload.status}}`);
  }}

  if (payload.command !== "bash scripts/check_public_connector_fixture_replay.sh") {{
    throw new Error(`unexpected connector replay command: ${{payload.command}}`);
  }}

  if (payload.fixtureFile !== "examples/connector-fixtures/replay-fixtures.sanitized.json") {{
    throw new Error(`unexpected connector replay fixtureFile: ${{payload.fixtureFile}}`);
  }}

  if (!Array.isArray(payload.outcomes) || payload.outcomes.length < 6) {{
    throw new Error("connector replay outcomes are missing or too short");
  }}

  const groups = new Set(payload.outcomes.map((item) => item?.group));
  const requiredGroups = [
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
  ];
  for (const group of requiredGroups) {{
    if (!groups.has(group)) {{
      throw new Error(`connector replay group is missing: ${{group}}`);
    }}
  }}

  if (!Array.isArray(payload.boundaries) || payload.boundaries.length < 4) {{
    throw new Error("connector replay boundaries are missing or too short");
  }}

  const boundaryNames = new Set(payload.boundaries.map((item) => item?.name));
  for (const boundary of ["raw payload", "credentials", "external calls", "persistence"]) {{
    if (!boundaryNames.has(boundary)) {{
      throw new Error(`connector replay boundary is missing: ${{boundary}}`);
    }}
  }}

  if (!Array.isArray(payload.docs) || payload.docs.length < 3) {{
    throw new Error("connector replay docs are missing or too short");
  }}
}}

export function validateConnectorCertificationPayload(payload) {{
  const missing = CONNECTOR_CERTIFICATION_REQUIRED_FIELDS.filter((field) => !(field in (payload || {{}})));
  if (missing.length > 0) {{
    throw new Error(`missing connector certification fields: ${{missing.join(", ")}}`);
  }}

  if (payload.status !== "validated") {{
    throw new Error(`unexpected connector certification status: ${{payload.status}}`);
  }}

  if (payload.command !== `GET ${{CONNECTOR_CERTIFICATION_PATH}}`) {{
    throw new Error(`unexpected connector certification command: ${{payload.command}}`);
  }}

  if (payload.certificationLevel !== "public_contract_certified") {{
    throw new Error(`unexpected connector certification level: ${{payload.certificationLevel}}`);
  }}

  if (!Array.isArray(payload.providerProfiles) || payload.providerProfiles.length < 3) {{
    throw new Error("connector certification provider profiles are missing or too short");
  }}

  const providerKeys = new Set(payload.providerProfiles.map((item) => item?.adapterKey));
  for (const requiredKey of ["crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"]) {{
    if (!providerKeys.has(requiredKey)) {{
      throw new Error(`connector certification provider key missing: ${{requiredKey}}`);
    }}
  }}

  if (!Array.isArray(payload.certificationStages) || payload.certificationStages.length < 6) {{
    throw new Error("connector certification stages are missing or too short");
  }}

  if (!Array.isArray(payload.certificationGates) || payload.certificationGates.length < 5) {{
    throw new Error("connector certification gates are missing or too short");
  }}

  if (payload.certificationGates.some((item) => item?.externalMutation !== false)) {{
    throw new Error("connector certification gates must not mutate external providers");
  }}

  if (!Array.isArray(payload.dataBoundaries) || payload.dataBoundaries.length < 3) {{
    throw new Error("connector certification data boundaries are missing or too short");
  }}
}}

export function validateProviderOnboardingPayload(payload) {{
  const missing = PROVIDER_ONBOARDING_REQUIRED_FIELDS.filter((field) => !(field in (payload || {{}})));
  if (missing.length > 0) {{
    throw new Error(`missing provider onboarding fields: ${{missing.join(", ")}}`);
  }}

  if (payload.status !== "previewed") {{
    throw new Error(`unexpected provider onboarding status: ${{payload.status}}`);
  }}

  if (payload.command !== `GET ${{PROVIDER_ONBOARDING_PATH}}`) {{
    throw new Error(`unexpected provider onboarding command: ${{payload.command}}`);
  }}

  if (payload.onboardingLevel !== "sandbox_onboarding_ready") {{
    throw new Error(`unexpected provider onboarding level: ${{payload.onboardingLevel}}`);
  }}

  if (payload.providerKey !== "crm.bitrix24.mock") {{
    throw new Error(`unexpected provider onboarding key: ${{payload.providerKey}}`);
  }}

  for (const key of ["summary", "onboardingStages", "preflightChecks", "rolloutPlan", "dataBoundaries"]) {{
    if (!Array.isArray(payload[key]) || payload[key].length === 0) {{
      throw new Error(`provider onboarding ${{key}} is missing or empty`);
    }}
  }}

  if (!payload.sandboxContract || payload.sandboxContract.providerCallEnabled !== false) {{
    throw new Error("provider onboarding sandbox contract must not call providers");
  }}

  if (payload.dataBoundaries.some((item) => item?.externalMutation !== false)) {{
    throw new Error("provider onboarding boundaries must not mutate external providers");
  }}
}}

export function validateBusinessScenarioReplayPayload(payload) {{
  const missing = BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {{
    throw new Error(`missing business scenario replay fields: ${{missing.join(", ")}}`);
  }}

  if (payload.status !== "validated") {{
    throw new Error(`unexpected business scenario replay status: ${{payload.status}}`);
  }}

  if (payload.command !== "bash scripts/check_public_business_scenario_replay.sh") {{
    throw new Error(`unexpected business scenario replay command: ${{payload.command}}`);
  }}

  if (!Array.isArray(payload.scenarios) || payload.scenarios.length < 3) {{
    throw new Error("business scenario replay scenarios are missing or too short");
  }}

  const scenarioIds = new Set(payload.scenarios.map((item) => item?.id));
  for (const scenarioId of ["crm-bank-payment-mismatch", "support-sla-risk", "procurement-delay-risk"]) {{
    if (!scenarioIds.has(scenarioId)) {{
      throw new Error(`business scenario replay scenario is missing: ${{scenarioId}}`);
    }}
  }}

  for (const scenario of payload.scenarios) {{
    if (!Array.isArray(scenario?.normalizedFacts) || scenario.normalizedFacts.length === 0) {{
      throw new Error(`business scenario replay facts missing: ${{scenario?.id}}`);
    }}
    if (!Array.isArray(scenario?.recommendedActions) || scenario.recommendedActions.length === 0) {{
      throw new Error(`business scenario replay actions missing: ${{scenario?.id}}`);
    }}
    if (!Array.isArray(scenario?.automationCandidates) || !scenario.automationCandidates.some((item) => item?.safeToAutoRun === false)) {{
      throw new Error(`business scenario replay lacks approval boundary: ${{scenario?.id}}`);
    }}
  }}

  if (!Array.isArray(payload.flow) || payload.flow.length < 5) {{
    throw new Error("business scenario replay flow is missing or too short");
  }}

  if (!Array.isArray(payload.docs) || payload.docs.length < 4) {{
    throw new Error("business scenario replay docs are missing or too short");
  }}
}}

export function validatePublicDemoPayload(payload) {{
  const missing = REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {{
    throw new Error(`missing required fields: ${{missing.join(", ")}}`);
  }}

  if (payload.schemaVersion !== 1) {{
    throw new Error(`unexpected schemaVersion: ${{payload.schemaVersion}}`);
  }}

  if (payload.dataSource !== "api.synthetic") {{
    throw new Error(`unexpected dataSource: ${{payload.dataSource}}`);
  }}

  if (payload.apiContract?.path !== PUBLIC_DEMO_PATH) {{
    throw new Error(`unexpected apiContract.path: ${{payload.apiContract?.path}}`);
  }}

  if (payload.tenant?.slug !== "demo-academy") {{
    throw new Error(`unexpected tenant.slug: ${{payload.tenant?.slug}}`);
  }}

  if (payload.workflow?.id !== "wf-demo-lead-to-student") {{
    throw new Error(`unexpected workflow.id: ${{payload.workflow?.id}}`);
  }}

  if (payload.workflow?.currentStage !== "student_sync") {{
    throw new Error(`unexpected workflow.currentStage: ${{payload.workflow?.currentStage}}`);
  }}

  if (!Array.isArray(payload.workflow?.stages) || payload.workflow.stages.length < 5) {{
    throw new Error("workflow.stages is missing or too short");
  }}

  if (!Array.isArray(payload.workflowScenarios) || payload.workflowScenarios.length < 3) {{
    throw new Error("workflowScenarios is missing or too short");
  }}

  const scenarioIds = new Set(payload.workflowScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of ["scenario-contract-approval-sync", "scenario-signature-task", "scenario-accounting-export"]) {{
    if (!scenarioIds.has(requiredScenario)) {{
      throw new Error(`workflowScenarios does not include required scenario: ${{requiredScenario}}`);
    }}
  }}

  const actionTypes = new Set(payload.workflowScenarios.map((scenario) => scenario?.actionType));
  for (const requiredAction of ["emit_outbox_event", "create_task_record", "request_adapter_sync"]) {{
    if (!actionTypes.has(requiredAction)) {{
      throw new Error(`workflowScenarios does not include required action: ${{requiredAction}}`);
    }}
  }}

  const scenarioOutputs = new Set(payload.workflowScenarios.flatMap((scenario) => scenario?.outputs || []));
  for (const requiredOutput of ["audit_event", "outbox_event", "task_record", "integration_job", "action_run"]) {{
    if (!scenarioOutputs.has(requiredOutput)) {{
      throw new Error(`workflowScenarios does not include required output: ${{requiredOutput}}`);
    }}
  }}

  if (!Array.isArray(payload.adapterScenarios) || payload.adapterScenarios.length < 6) {{
    throw new Error("adapterScenarios is missing or too short");
  }}

  const adapterScenarioIds = new Set(payload.adapterScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of [
    "adapter-file-import-preview",
    "adapter-file-import-execute",
    "adapter-crm-deal-preview",
    "adapter-crm-deal-ingest",
    "adapter-accounting-export-retry",
    "adapter-dead-letter-review",
  ]) {{
    if (!adapterScenarioIds.has(requiredScenario)) {{
      throw new Error(`adapterScenarios does not include required scenario: ${{requiredScenario}}`);
    }}
  }}

  const adapterPhases = new Set(payload.adapterScenarios.map((scenario) => scenario?.phase));
  for (const requiredPhase of ["preview", "execute", "retry", "operator_review"]) {{
    if (!adapterPhases.has(requiredPhase)) {{
      throw new Error(`adapterScenarios does not include required phase: ${{requiredPhase}}`);
    }}
  }}

  const adapterOutputs = new Set(payload.adapterScenarios.flatMap((scenario) => scenario?.outputs || []));
  for (const requiredOutput of [
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
  ]) {{
    if (!adapterOutputs.has(requiredOutput)) {{
      throw new Error(`adapterScenarios does not include required output: ${{requiredOutput}}`);
    }}
  }}

  for (const key of ["summary", "flow", "operationPlans", "boundaries", "diagnostics", "docs"]) {{
    if (!Array.isArray(payload.adapterStudio?.[key]) || payload.adapterStudio[key].length === 0) {{
      throw new Error(`adapterStudio.${{key}} is missing or empty`);
    }}
  }}

  const adapterStudioPlans = new Map(payload.adapterStudio.operationPlans.map((item) => [item?.scenarioId, item]));
  for (const requiredPlan of ["adapter-crm-deal-preview", "adapter-crm-deal-ingest"]) {{
    if (!adapterStudioPlans.has(requiredPlan)) {{
      throw new Error(`adapterStudio.operationPlans does not include required plan: ${{requiredPlan}}`);
    }}
  }}

  if (adapterStudioPlans.get("adapter-crm-deal-preview")?.executionMode !== "contract_only") {{
    throw new Error("adapterStudio CRM preview plan must be contract_only");
  }}

  if (adapterStudioPlans.get("adapter-crm-deal-preview")?.safeToRunAgainstPublicDemo !== false) {{
    throw new Error("adapterStudio CRM preview plan must not be marked safe for live public execution");
  }}

  if (adapterStudioPlans.get("adapter-crm-deal-ingest")?.method !== "WORKER") {{
    throw new Error("adapterStudio CRM ingest plan must be worker-backed");
  }}

  const adapterStudioBoundaryEvidence = new Set(payload.adapterStudio.boundaries.map((item) => item?.evidence));
  for (const requiredEvidence of ["server_secret_store", "private_connector_only", "redaction_evidence"]) {{
    if (!adapterStudioBoundaryEvidence.has(requiredEvidence)) {{
      throw new Error(`adapterStudio.boundaries does not include required evidence: ${{requiredEvidence}}`);
    }}
  }}

  if (!payload.connectorFixtureReplay || typeof payload.connectorFixtureReplay !== "object") {{
    throw new Error("connectorFixtureReplay is missing");
  }}
  validateConnectorFixtureReplayPayload(payload.connectorFixtureReplay);

  if (!payload.connectorCertification || typeof payload.connectorCertification !== "object") {{
    throw new Error("connectorCertification is missing");
  }}
  validateConnectorCertificationPayload(payload.connectorCertification);

  if (!payload.providerOnboarding || typeof payload.providerOnboarding !== "object") {{
    throw new Error("providerOnboarding is missing");
  }}
  validateProviderOnboardingPayload(payload.providerOnboarding);

  if (!payload.businessScenarioReplay || typeof payload.businessScenarioReplay !== "object") {{
    throw new Error("businessScenarioReplay is missing");
  }}
  validateBusinessScenarioReplayPayload(payload.businessScenarioReplay);

  if (payload.engineeringProof?.milestone !== "engineering_70") {{
    throw new Error(`unexpected engineeringProof.milestone: ${{payload.engineeringProof?.milestone}}`);
  }}

  if (!Array.isArray(payload.engineeringProof?.gates) || payload.engineeringProof.gates.length < 5) {{
    throw new Error("engineeringProof.gates is missing or too short");
  }}

  if (!Array.isArray(payload.alertRouting?.routes) || payload.alertRouting.routes.length < 3) {{
    throw new Error("alertRouting.routes is missing or too short");
  }}

  if (!Array.isArray(payload.alertRouting?.bindings) || payload.alertRouting.bindings.length < 5) {{
    throw new Error("alertRouting.bindings is missing or too short");
  }}

  const alertNames = new Set(payload.alertRouting.bindings.map((binding) => binding?.alert));
  for (const requiredAlert of ["DriveDeskApiTargetDown", "DriveDeskIntegrationDeadLetters", "DriveDeskScheduledValidationMissed"]) {{
    if (!alertNames.has(requiredAlert)) {{
      throw new Error(`alertRouting.bindings does not include required alert: ${{requiredAlert}}`);
    }}
  }}

  if (!Array.isArray(payload.incidentResponse?.incidents) || payload.incidentResponse.incidents.length < 3) {{
    throw new Error("incidentResponse.incidents is missing or too short");
  }}

  const incidentStatuses = new Set(payload.incidentResponse.incidents.map((incident) => incident?.status));
  for (const requiredStatus of ["open", "acknowledged", "resolved"]) {{
    if (!incidentStatuses.has(requiredStatus)) {{
      throw new Error(`incidentResponse.incidents does not include required status: ${{requiredStatus}}`);
    }}
  }}

  if (!Array.isArray(payload.incidentResponse?.timeline) || payload.incidentResponse.timeline.length < 5) {{
    throw new Error("incidentResponse.timeline is missing or too short");
  }}

  if (!Array.isArray(payload.domainEvents)) {{
    throw new Error("domainEvents is missing");
  }}

  const eventNames = new Set(payload.domainEvents.map((event) => event?.event));
  for (const requiredEvent of ["lead.created", "student.created", "contract.generated", "student.sync.requested"]) {{
    if (!eventNames.has(requiredEvent)) {{
      throw new Error(`domainEvents does not include required event: ${{requiredEvent}}`);
    }}
  }}
}}

async function main() {{
  const baseUrlIndex = process.argv.indexOf("--base-url");
  const baseUrl =
    baseUrlIndex >= 0 && process.argv[baseUrlIndex + 1]
      ? process.argv[baseUrlIndex + 1]
      : process.env.BASE_URL || "http://localhost:8080";
  const client = new DriveDeskPublicDemoClient(baseUrl);
  const payload = await client.getPublicDemo();
  const connectorReplay = await client.getConnectorFixtureReplay();
  const connectorCertification = await client.getConnectorCertification();
  const providerOnboarding = await client.getProviderOnboarding();
  const businessScenarioReplay = await client.getBusinessScenarioReplay();
  const adapterPlan = buildAdapterOperationPlan(payload, "adapter-file-import-preview");
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${{payload.workflow.currentStage}}`,
    `adapterPlan=${{adapterPlan.phase}}`,
    `connectorReplay=${{connectorReplay.status}}`,
    `connectorCertification=${{connectorCertification.certificationLevel}}`,
    `providerOnboarding=${{providerOnboarding.onboardingLevel}}`,
    `businessScenarioReplay=${{businessScenarioReplay.status}}`,
    `operation=${{OPERATION_ID}}`,
    `connectorOperation=${{CONNECTOR_REPLAY_OPERATION_ID}}`,
    `connectorCertificationOperation=${{CONNECTOR_CERTIFICATION_OPERATION_ID}}`,
    `providerOnboardingOperation=${{PROVIDER_ONBOARDING_OPERATION_ID}}`,
    `businessScenarioOperation=${{BUSINESS_SCENARIO_REPLAY_OPERATION_ID}}`,
  );
}}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {{
  main().catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
}}
'''


def render_typescript_defs(
    operation_id: str,
    required_fields: list[str],
    connector_operation_id: str,
    connector_required_fields: list[str],
    connector_certification_operation_id: str,
    connector_certification_required_fields: list[str],
    provider_onboarding_operation_id: str,
    provider_onboarding_required_fields: list[str],
    business_scenario_operation_id: str,
    business_scenario_required_fields: list[str],
) -> str:
    required_union = " | ".join(f'"{field}"' for field in required_fields)
    connector_required_union = " | ".join(f'"{field}"' for field in connector_required_fields)
    connector_certification_required_union = " | ".join(
        f'"{field}"' for field in connector_certification_required_fields
    )
    provider_onboarding_required_union = " | ".join(
        f'"{field}"' for field in provider_onboarding_required_fields
    )
    business_scenario_required_union = " | ".join(
        f'"{field}"' for field in business_scenario_required_fields
    )
    return f'''// Generated from DriveDesk Core OpenAPI. Do not edit by hand.
export const PUBLIC_DEMO_PATH: "{PUBLIC_DEMO_PATH}";
export const CONNECTOR_REPLAY_PATH: "{CONNECTOR_REPLAY_PATH}";
export const CONNECTOR_CERTIFICATION_PATH: "{CONNECTOR_CERTIFICATION_PATH}";
export const PROVIDER_ONBOARDING_PATH: "{PROVIDER_ONBOARDING_PATH}";
export const BUSINESS_SCENARIO_REPLAY_PATH: "{BUSINESS_SCENARIO_REPLAY_PATH}";
export const OPERATION_ID: "{operation_id}";
export const CONNECTOR_REPLAY_OPERATION_ID: "{connector_operation_id}";
export const CONNECTOR_CERTIFICATION_OPERATION_ID: "{connector_certification_operation_id}";
export const PROVIDER_ONBOARDING_OPERATION_ID: "{provider_onboarding_operation_id}";
export const BUSINESS_SCENARIO_REPLAY_OPERATION_ID: "{business_scenario_operation_id}";
export const REQUIRED_FIELDS: Array<{required_union}>;
export const CONNECTOR_REPLAY_REQUIRED_FIELDS: Array<{connector_required_union}>;
export const CONNECTOR_CERTIFICATION_REQUIRED_FIELDS: Array<{connector_certification_required_union}>;
export const PROVIDER_ONBOARDING_REQUIRED_FIELDS: Array<{provider_onboarding_required_union}>;
export const BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS: Array<{business_scenario_required_union}>;

export type AdapterScenarioPhase = "preview" | "execute" | "retry" | "operator_review";

export interface AdapterScenario {{
  id: string;
  title: string;
  adapter: "file.import.fake" | "crm.bitrix24.mock" | "accounting.export.mock" | string;
  operation: string;
  phase: AdapterScenarioPhase;
  endpoint: string;
  requiredScope: string;
  status: string;
  detail: string;
  inputs: string[];
  outputs: string[];
  evidence: string;
}}

export interface AdapterOperationPlan {{
  scenarioId: string;
  adapter: string;
  operation: string;
  phase: AdapterScenarioPhase;
  executionMode: "contract_only";
  safeToRunAgainstPublicDemo: false;
  request: {{
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "WORKER";
    path: string;
    headers: Record<string, string>;
    body: Record<string, unknown> | null;
  }};
  expectedResponse: {{
    status: string;
    outputs: string[];
    evidence: string;
    sideEffects: string[];
  }};
}}

export interface ConnectorFixtureReplayPayload {{
  status: "validated";
  command: string;
  fixtureFile: string;
  evidenceFile: string;
  summary: Array<Record<string, unknown>>;
  outcomes: Array<{{
    group: string;
    stage: string;
    status: string;
    detail: string;
    evidence: string;
  }}>;
  boundaries: Array<Record<string, unknown>>;
  docs: Array<Record<string, string>>;
}}

export interface ConnectorCertificationPayload {{
  status: "validated";
  command: string;
  certificationLevel: "public_contract_certified";
  adapterCount: number;
  privateReadyCount: number;
  summary: Array<Record<string, unknown>>;
  providerProfiles: Array<Record<string, unknown>>;
  certificationStages: Array<Record<string, unknown>>;
  certificationGates: Array<Record<string, unknown>>;
  implementationPath: Array<Record<string, unknown>>;
  dataBoundaries: Array<Record<string, unknown>>;
  api: Record<string, string>;
  docs: Array<Record<string, string>>;
}}

export interface ProviderOnboardingPayload {{
  status: "previewed";
  command: string;
  onboardingLevel: "sandbox_onboarding_ready";
  providerKey: string;
  providerName: string;
  providerCategory: string;
  summary: Array<Record<string, unknown>>;
  providerProfile: Record<string, unknown>;
  onboardingStages: Array<Record<string, unknown>>;
  mappingPreview: Record<string, unknown>;
  preflightChecks: Array<Record<string, unknown>>;
  sandboxContract: Record<string, unknown>;
  rolloutPlan: Array<Record<string, unknown>>;
  dataBoundaries: Array<Record<string, unknown>>;
  api: Record<string, string>;
  docs: Array<Record<string, string>>;
}}

export interface BusinessScenarioReplayPayload {{
  status: "validated";
  command: string;
  summary: Array<Record<string, unknown>>;
  scenarios: Array<{{
    id: string;
    title: string;
    status: string;
    riskLevel: string;
    operatorRole: string;
    trigger: string;
    decision: string;
    sourceSystems: string[];
    normalizedFacts: Array<Record<string, string>>;
    recommendedActions: Array<Record<string, string>>;
    automationCandidates: Array<Record<string, unknown>>;
    evidence: string[];
    dataBoundary: string[];
  }}>;
  flow: Array<Record<string, string>>;
  docs: Array<Record<string, string>>;
}}

export interface PublicDemoPayload {{
  schemaVersion: 1;
  generatedAt: string;
  dataSource: "api.synthetic";
  apiContract: Record<string, string>;
  tenant: Record<string, string>;
  health: Record<string, string>;
  metrics: Array<Record<string, unknown>>;
  workQueue: Array<Record<string, unknown>>;
  members: Array<Record<string, string>>;
  auditEvents: Array<Record<string, string>>;
  outbox: Array<Record<string, unknown>>;
  adapters: Array<Record<string, string>>;
  adapterScenarios: AdapterScenario[];
  adapterStudio: Record<string, unknown>;
  connectorCertification: ConnectorCertificationPayload;
  providerOnboarding: ProviderOnboardingPayload;
  connectorFixtureReplay: ConnectorFixtureReplayPayload;
  integrationJobs: Array<Record<string, unknown>>;
  integrationHealth: Array<Record<string, string>>;
  integrationReadiness: Array<Record<string, unknown>>;
  recoveryEvidence: Array<Record<string, string>>;
  alertRouting: {{
    summary: Array<Record<string, string>>;
    routes: Array<Record<string, string>>;
    bindings: Array<Record<string, string>>;
    runbookActions: Array<Record<string, string>>;
  }};
  incidentResponse: {{
    summary: Array<Record<string, string>>;
    incidents: Array<Record<string, string>>;
    timeline: Array<Record<string, string>>;
    recoveryActions: Array<Record<string, string>>;
    resolutionEvidence: Array<Record<string, string>>;
  }};
  businessScenarioReplay: BusinessScenarioReplayPayload;
  engineeringProof: {{
    milestone: "engineering_70";
    status: "validated";
    updatedAt: string;
    summary: Array<Record<string, string>>;
    gates: Array<Record<string, string>>;
    evidence: Array<Record<string, string>>;
  }};
  workflow: {{
    id: "wf-demo-lead-to-student";
    currentStage: "student_sync";
    stages: Array<Record<string, string>>;
    [key: string]: unknown;
  }};
  workflowScenarios: Array<{{
    id: string;
    title: string;
    trigger: string;
    actionType: "emit_outbox_event" | "create_task_record" | "request_adapter_sync";
    owner: string;
    status: string;
    detail: string;
    outputs: string[];
    evidence: string;
  }}>;
  timeline: Array<Record<string, string>>;
  domainEvents: Array<Record<string, string>>;
}}

export class DriveDeskPublicDemoClient {{
  constructor(baseUrl?: string, options?: {{ fetchImpl?: typeof fetch }});
  getPublicDemo(): Promise<PublicDemoPayload>;
  getConnectorFixtureReplay(): Promise<ConnectorFixtureReplayPayload>;
  getConnectorCertification(): Promise<ConnectorCertificationPayload>;
  getProviderOnboarding(): Promise<ProviderOnboardingPayload>;
  getBusinessScenarioReplay(): Promise<BusinessScenarioReplayPayload>;
  getAdapterOperationPlan(
    scenarioId: string,
    options?: {{ requestId?: string }},
  ): Promise<AdapterOperationPlan>;
}}

export function getAdapterScenario(payload: PublicDemoPayload, scenarioId: string): AdapterScenario;
export function buildAdapterOperationPlan(
  payload: PublicDemoPayload,
  scenarioId: string,
  options?: {{ requestId?: string }},
): AdapterOperationPlan;
export function validatePublicDemoPayload(payload: PublicDemoPayload): void;
export function validateConnectorFixtureReplayPayload(payload: ConnectorFixtureReplayPayload): void;
export function validateConnectorCertificationPayload(payload: ConnectorCertificationPayload): void;
export function validateProviderOnboardingPayload(payload: ProviderOnboardingPayload): void;
export function validateBusinessScenarioReplayPayload(payload: BusinessScenarioReplayPayload): void;
'''


def render_readme(
    operation_id: str,
    connector_operation_id: str,
    connector_certification_operation_id: str,
    provider_onboarding_operation_id: str,
    business_notification_channels_operation_id: str,
    business_context_assistant_operation_id: str,
    business_action_execution_operation_id: str,
    business_approval_gateway_operation_id: str,
    integration_runtime_operation_id: str,
    integration_execution_operation_id: str,
    business_scenario_operation_id: str,
) -> str:
    return f'''# Generated Public Demo SDK

This folder is generated from `docs/openapi.json` by:

```bash
python scripts/generate_public_demo_sdk.py --openapi docs/openapi.json --out sdk/generated/public-demo
```

Generated clients:

- `python/drivedesk_public_demo_client.py`
- `javascript/drivedesk-public-demo-client.mjs`
- `typescript/drivedesk-public-demo-client.d.ts`

The clients target:

```text
GET {PUBLIC_DEMO_PATH}
operationId: {operation_id}

GET {CONNECTOR_REPLAY_PATH}
operationId: {connector_operation_id}

GET {CONNECTOR_CERTIFICATION_PATH}
operationId: {connector_certification_operation_id}

GET {PROVIDER_ONBOARDING_PATH}
operationId: {provider_onboarding_operation_id}

GET {BUSINESS_NOTIFICATION_CHANNELS_PATH}
operationId: {business_notification_channels_operation_id}

GET {BUSINESS_CONTEXT_ASSISTANT_PATH}
operationId: {business_context_assistant_operation_id}

GET {BUSINESS_ACTION_EXECUTION_PATH}
operationId: {business_action_execution_operation_id}

GET {BUSINESS_APPROVAL_GATEWAY_PATH}
operationId: {business_approval_gateway_operation_id}

GET {INTEGRATION_RUNTIME_PATH}
operationId: {integration_runtime_operation_id}

GET {INTEGRATION_EXECUTION_PATH}
operationId: {integration_execution_operation_id}

GET {BUSINESS_SCENARIO_REPLAY_PATH}
operationId: {business_scenario_operation_id}
```

Run the SDK smoke:

```bash
bash scripts/check_public_demo_sdk.sh
```

Adapter operation helpers:

- `getAdapterScenario` / `get_adapter_scenario`
- `buildAdapterOperationPlan` / `build_adapter_operation_plan`
- `DriveDeskPublicDemoClient.getAdapterOperationPlan`
- `DriveDeskPublicDemoClient.get_adapter_operation_plan`
- `DriveDeskPublicDemoClient.getConnectorFixtureReplay`
- `DriveDeskPublicDemoClient.get_connector_fixture_replay`
- `DriveDeskPublicDemoClient.getConnectorCertification`
- `DriveDeskPublicDemoClient.get_connector_certification`
- `connector_certification` manifest entry for
  `GET {CONNECTOR_CERTIFICATION_PATH}`
- `DriveDeskPublicDemoClient.getProviderOnboarding`
- `DriveDeskPublicDemoClient.get_provider_onboarding`
- `provider_onboarding` manifest entry for
  `GET {PROVIDER_ONBOARDING_PATH}`
- `business_notification_channels` manifest entry for
  `GET {BUSINESS_NOTIFICATION_CHANNELS_PATH}`
- `business_context_assistant` manifest entry for
  `GET {BUSINESS_CONTEXT_ASSISTANT_PATH}`
- `business_action_execution` manifest entry for
  `GET {BUSINESS_ACTION_EXECUTION_PATH}`
- `business_approval_gateway` manifest entry for
  `GET {BUSINESS_APPROVAL_GATEWAY_PATH}`
- `integration_runtime` manifest entry for
  `GET {INTEGRATION_RUNTIME_PATH}`
- `integration_execution` manifest entry for
  `GET {INTEGRATION_EXECUTION_PATH}`
- `DriveDeskPublicDemoClient.getBusinessScenarioReplay`
- `DriveDeskPublicDemoClient.get_business_scenario_replay`

These helpers turn the public `adapterScenarios` payload into a typed
contract-only request/response plan for mapping preview, execution, retry, and
operator-review flows. They do not mutate the public demo.

Connector fixture replay helpers validate the public-safe replay evidence as a
standalone API contract: fixture groups, redaction outcomes, boundaries, and
review docs.

Connector certification helpers validate the public-safe provider-readiness
workbench: provider profiles, certification stages, gates, implementation path,
data boundaries, and review docs.

Provider onboarding helpers validate the sandbox-to-private rollout path:
connection profile, mapping preview, preflight checks, sandbox contract, rollout
plan, and provider data boundaries.

Business scenario replay helpers validate the Business OS scenario contract:
source systems, normalized facts, recommended actions, automation boundaries,
and replay docs.

Business notification channel metadata validates the public-safe channel matrix:
in-app readiness, draft-only external channels, private secret gates, and no
external delivery.

Business Context Assistant metadata validates the public-safe context surface:
CRM, bank, accounting, and legal-reference facts become safe context cards,
insight rules, and next actions through `businessContextAssistant`.

Business action execution metadata validates the public-safe execution preview:
idempotency keys, preflight checks, dry-run results, approval gates, rollback
notes, and explicit no-provider-write boundaries.

Business approval gateway metadata validates the public-safe approval preview:
approval requests, RBAC and dual-control checks, approver routing, blocked
commit unlocks, and explicit no-provider-write boundaries.

Integration runtime metadata validates the public-safe adapter runtime:
operation contract selection, scope and idempotency preflight, outbox handoff,
worker boundary, reconciliation planning, incident routing, and no provider
calls in the public demo.

Integration execution metadata validates the public-safe execution timeline:
run ledger, outbox enqueue, worker dispatch, blocked provider call, retry,
dead-letter, reconciliation, observability, and no raw provider payloads.

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
'''


def render_manifest(
    operation_id: str,
    required_fields: list[str],
    connector_operation_id: str,
    connector_required_fields: list[str],
    connector_certification_operation_id: str,
    connector_certification_required_fields: list[str],
    provider_onboarding_operation_id: str,
    provider_onboarding_required_fields: list[str],
    business_intake_operation_id: str,
    business_intake_required_fields: list[str],
    business_task_handoff_operation_id: str,
    business_task_handoff_required_fields: list[str],
    business_notification_channels_operation_id: str,
    business_notification_channels_required_fields: list[str],
    business_context_assistant_operation_id: str,
    business_context_assistant_required_fields: list[str],
    business_action_execution_operation_id: str,
    business_action_execution_required_fields: list[str],
    business_approval_gateway_operation_id: str,
    business_approval_gateway_required_fields: list[str],
    integration_runtime_operation_id: str,
    integration_runtime_required_fields: list[str],
    integration_execution_operation_id: str,
    integration_execution_required_fields: list[str],
    business_scenario_operation_id: str,
    business_scenario_required_fields: list[str],
) -> str:
    payload = {
        "schema_version": 1,
        "source": "docs/openapi.json",
        "path": PUBLIC_DEMO_PATH,
        "method": PUBLIC_DEMO_METHOD.upper(),
        "operation_id": operation_id,
        "connector_replay": {
            "path": CONNECTOR_REPLAY_PATH,
            "method": CONNECTOR_REPLAY_METHOD.upper(),
            "operation_id": connector_operation_id,
            "required_fields": connector_required_fields,
        },
        "connector_certification": {
            "path": CONNECTOR_CERTIFICATION_PATH,
            "method": CONNECTOR_CERTIFICATION_METHOD.upper(),
            "operation_id": connector_certification_operation_id,
            "required_fields": connector_certification_required_fields,
        },
        "provider_onboarding": {
            "path": PROVIDER_ONBOARDING_PATH,
            "method": PROVIDER_ONBOARDING_METHOD.upper(),
            "operation_id": provider_onboarding_operation_id,
            "required_fields": provider_onboarding_required_fields,
        },
        "business_intake_pipeline": {
            "path": BUSINESS_INTAKE_PIPELINE_PATH,
            "method": BUSINESS_INTAKE_PIPELINE_METHOD.upper(),
            "operation_id": business_intake_operation_id,
            "required_fields": business_intake_required_fields,
        },
        "business_task_handoff": {
            "path": BUSINESS_TASK_HANDOFF_PATH,
            "method": BUSINESS_TASK_HANDOFF_METHOD.upper(),
            "operation_id": business_task_handoff_operation_id,
            "required_fields": business_task_handoff_required_fields,
        },
        "business_notification_channels": {
            "path": BUSINESS_NOTIFICATION_CHANNELS_PATH,
            "method": BUSINESS_NOTIFICATION_CHANNELS_METHOD.upper(),
            "operation_id": business_notification_channels_operation_id,
            "required_fields": business_notification_channels_required_fields,
        },
        "business_context_assistant": {
            "path": BUSINESS_CONTEXT_ASSISTANT_PATH,
            "method": BUSINESS_CONTEXT_ASSISTANT_METHOD.upper(),
            "operation_id": business_context_assistant_operation_id,
            "required_fields": business_context_assistant_required_fields,
        },
        "business_action_execution": {
            "path": BUSINESS_ACTION_EXECUTION_PATH,
            "method": BUSINESS_ACTION_EXECUTION_METHOD.upper(),
            "operation_id": business_action_execution_operation_id,
            "required_fields": business_action_execution_required_fields,
        },
        "business_approval_gateway": {
            "path": BUSINESS_APPROVAL_GATEWAY_PATH,
            "method": BUSINESS_APPROVAL_GATEWAY_METHOD.upper(),
            "operation_id": business_approval_gateway_operation_id,
            "required_fields": business_approval_gateway_required_fields,
        },
        "integration_runtime": {
            "path": INTEGRATION_RUNTIME_PATH,
            "method": INTEGRATION_RUNTIME_METHOD.upper(),
            "operation_id": integration_runtime_operation_id,
            "required_fields": integration_runtime_required_fields,
        },
        "integration_execution": {
            "path": INTEGRATION_EXECUTION_PATH,
            "method": INTEGRATION_EXECUTION_METHOD.upper(),
            "operation_id": integration_execution_operation_id,
            "required_fields": integration_execution_required_fields,
        },
        "business_scenario_replay": {
            "path": BUSINESS_SCENARIO_REPLAY_PATH,
            "method": BUSINESS_SCENARIO_REPLAY_METHOD.upper(),
            "operation_id": business_scenario_operation_id,
            "required_fields": business_scenario_required_fields,
        },
        "data_profile": "synthetic_demo_data",
        "generated_files": [
            "README.md",
            "openapi-client-manifest.json",
            "python/drivedesk_public_demo_client.py",
            "javascript/drivedesk-public-demo-client.mjs",
            "typescript/drivedesk-public-demo-client.d.ts",
        ],
        "required_fields": required_fields,
        "adapter_helper_scenarios": [
            "adapter-file-import-preview",
            "adapter-file-import-execute",
            "adapter-crm-deal-preview",
            "adapter-crm-deal-ingest",
            "adapter-accounting-export-retry",
            "adapter-dead-letter-review",
        ],
        "adapter_helper_phases": ["preview", "execute", "retry", "operator_review"],
        "adapter_helper_mode": "contract_only",
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def generate(openapi_path: Path, out_dir: Path) -> None:
    schema = load_schema(openapi_path)
    operation = public_demo_operation(schema)
    operation_id = str(operation.get("operationId") or "get_public_demo")
    required_fields = public_demo_required_fields(schema)
    connector_operation = connector_replay_operation(schema)
    connector_operation_id = str(
        connector_operation.get("operationId") or "get_connector_fixture_replay"
    )
    connector_required_fields = connector_replay_required_fields(schema)
    connector_certification_op = connector_certification_operation(schema)
    connector_certification_operation_id = str(
        connector_certification_op.get("operationId") or "get_connector_certification"
    )
    connector_certification_fields = connector_certification_required_fields(schema)
    provider_onboarding_op = provider_onboarding_operation(schema)
    provider_onboarding_operation_id = str(
        provider_onboarding_op.get("operationId") or "get_provider_onboarding"
    )
    provider_onboarding_fields = provider_onboarding_required_fields(schema)
    business_intake_operation = business_intake_pipeline_operation(schema)
    business_intake_operation_id = str(
        business_intake_operation.get("operationId") or "get_business_intake_pipeline"
    )
    business_intake_required_fields = business_intake_pipeline_required_fields(schema)
    business_task_handoff_op = business_task_handoff_operation(schema)
    business_task_handoff_operation_id = str(
        business_task_handoff_op.get("operationId") or "get_business_task_handoff"
    )
    business_task_handoff_fields = business_task_handoff_required_fields(schema)
    business_notification_channels_op = business_notification_channels_operation(schema)
    business_notification_channels_operation_id = str(
        business_notification_channels_op.get("operationId")
        or "get_business_notification_channels"
    )
    business_notification_channels_fields = business_notification_channels_required_fields(schema)
    business_context_assistant_op = business_context_assistant_operation(schema)
    business_context_assistant_operation_id = str(
        business_context_assistant_op.get("operationId")
        or "get_business_context_assistant"
    )
    business_context_assistant_fields = business_context_assistant_required_fields(schema)
    business_action_execution_op = business_action_execution_operation(schema)
    business_action_execution_operation_id = str(
        business_action_execution_op.get("operationId")
        or "get_business_action_execution"
    )
    business_action_execution_fields = business_action_execution_required_fields(schema)
    business_approval_gateway_op = business_approval_gateway_operation(schema)
    business_approval_gateway_operation_id = str(
        business_approval_gateway_op.get("operationId")
        or "get_business_approval_gateway"
    )
    business_approval_gateway_fields = business_approval_gateway_required_fields(schema)
    integration_runtime_op = integration_runtime_operation(schema)
    integration_runtime_operation_id = str(
        integration_runtime_op.get("operationId") or "get_integration_runtime"
    )
    integration_runtime_fields = integration_runtime_required_fields(schema)
    integration_execution_op = integration_execution_operation(schema)
    integration_execution_operation_id = str(
        integration_execution_op.get("operationId") or "get_integration_execution"
    )
    integration_execution_fields = integration_execution_required_fields(schema)
    business_scenario_operation = business_scenario_replay_operation(schema)
    business_scenario_operation_id = str(
        business_scenario_operation.get("operationId") or "get_business_scenario_replay"
    )
    business_scenario_required_fields = business_scenario_replay_required_fields(schema)

    write(
        out_dir / "README.md",
        render_readme(
            operation_id,
            connector_operation_id,
            connector_certification_operation_id,
            provider_onboarding_operation_id,
            business_notification_channels_operation_id,
            business_context_assistant_operation_id,
            business_action_execution_operation_id,
            business_approval_gateway_operation_id,
            integration_runtime_operation_id,
            integration_execution_operation_id,
            business_scenario_operation_id,
        ),
    )
    write(
        out_dir / "openapi-client-manifest.json",
        render_manifest(
            operation_id,
            required_fields,
            connector_operation_id,
            connector_required_fields,
            connector_certification_operation_id,
            connector_certification_fields,
            provider_onboarding_operation_id,
            provider_onboarding_fields,
            business_intake_operation_id,
            business_intake_required_fields,
            business_task_handoff_operation_id,
            business_task_handoff_fields,
            business_notification_channels_operation_id,
            business_notification_channels_fields,
            business_context_assistant_operation_id,
            business_context_assistant_fields,
            business_action_execution_operation_id,
            business_action_execution_fields,
            business_approval_gateway_operation_id,
            business_approval_gateway_fields,
            integration_runtime_operation_id,
            integration_runtime_fields,
            integration_execution_operation_id,
            integration_execution_fields,
            business_scenario_operation_id,
            business_scenario_required_fields,
        ),
    )
    write(
        out_dir / "python/drivedesk_public_demo_client.py",
        render_python_client(
            operation_id,
            required_fields,
            connector_operation_id,
            connector_required_fields,
            connector_certification_operation_id,
            connector_certification_fields,
            provider_onboarding_operation_id,
            provider_onboarding_fields,
            business_scenario_operation_id,
            business_scenario_required_fields,
        ),
    )
    write(
        out_dir / "javascript/drivedesk-public-demo-client.mjs",
        render_javascript_client(
            operation_id,
            required_fields,
            connector_operation_id,
            connector_required_fields,
            connector_certification_operation_id,
            connector_certification_fields,
            provider_onboarding_operation_id,
            provider_onboarding_fields,
            business_scenario_operation_id,
            business_scenario_required_fields,
        ),
    )
    write(
        out_dir / "typescript/drivedesk-public-demo-client.d.ts",
        render_typescript_defs(
            operation_id,
            required_fields,
            connector_operation_id,
            connector_required_fields,
            connector_certification_operation_id,
            connector_certification_fields,
            provider_onboarding_operation_id,
            provider_onboarding_fields,
            business_scenario_operation_id,
            business_scenario_required_fields,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public demo clients from DriveDesk OpenAPI.")
    parser.add_argument("--openapi", type=Path, default=Path("docs/openapi.json"))
    parser.add_argument("--out", type=Path, default=Path("sdk/generated/public-demo"))
    args = parser.parse_args()

    generate(args.openapi, args.out)
    print(f"generated public demo SDK: {args.out}")


if __name__ == "__main__":
    main()
