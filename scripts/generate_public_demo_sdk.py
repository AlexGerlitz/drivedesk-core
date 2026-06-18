#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PUBLIC_DEMO_PATH = "/demo/public"
PUBLIC_DEMO_METHOD = "get"


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def public_demo_operation(schema: dict[str, Any]) -> dict[str, Any]:
    paths = schema.get("paths", {})
    operation = paths.get(PUBLIC_DEMO_PATH, {}).get(PUBLIC_DEMO_METHOD)
    if not isinstance(operation, dict):
        raise SystemExit(f"OpenAPI schema does not contain GET {PUBLIC_DEMO_PATH}")
    return operation


def public_demo_required_fields(schema: dict[str, Any]) -> list[str]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    public_demo = schemas.get("PublicDemoRead", {})
    required = public_demo.get("required", [])
    if not isinstance(required, list) or not required:
        raise SystemExit("OpenAPI schema does not contain PublicDemoRead.required")
    return [str(item) for item in required]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_python_client(operation_id: str, required_fields: list[str]) -> str:
    required_json = json.dumps(required_fields, indent=2)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from typing import Any


PUBLIC_DEMO_PATH = "{PUBLIC_DEMO_PATH}"
OPERATION_ID = "{operation_id}"
REQUIRED_FIELDS = {required_json}


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
    parts = endpoint.strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0] in {{"GET", "POST", "PUT", "PATCH", "DELETE"}}:
        return parts[0], parts[1]
    raise ValueError(f"invalid adapter endpoint contract: {{endpoint}}")


def _adapter_operation_body(scenario: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    phase = scenario.get("phase")
    base = {{
        "requestId": request_id,
        "scenarioId": scenario.get("id"),
        "operation": scenario.get("operation"),
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
    if not isinstance(adapter_scenarios, list) or len(adapter_scenarios) < 4:
        raise ValueError("adapterScenarios is missing or too short")

    adapter_scenario_ids = {{scenario.get("id") for scenario in adapter_scenarios if isinstance(scenario, dict)}}
    required_adapter_scenarios = {{
        "adapter-file-import-preview",
        "adapter-file-import-execute",
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
        "retry_scheduled",
        "review_card",
        "manual_retry_endpoint",
    }}
    if not required_adapter_outputs.issubset(adapter_outputs):
        raise ValueError(
            f"adapterScenarios does not include required outputs: {{sorted(required_adapter_outputs - adapter_outputs)}}"
        )

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
    adapter_plan = build_adapter_operation_plan(payload, "adapter-file-import-preview")
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={{payload['workflow']['currentStage']}}",
        f"adapterPlan={{adapter_plan['phase']}}",
        f"operation={{OPERATION_ID}}",
    )


if __name__ == "__main__":
    main()
'''


def render_javascript_client(operation_id: str, required_fields: list[str]) -> str:
    required_json = json.dumps(required_fields, indent=2)
    return f'''#!/usr/bin/env node
import {{ pathToFileURL }} from "node:url";

export const PUBLIC_DEMO_PATH = "{PUBLIC_DEMO_PATH}";
export const OPERATION_ID = "{operation_id}";
export const REQUIRED_FIELDS = {required_json};

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

  if (!Array.isArray(payload.adapterScenarios) || payload.adapterScenarios.length < 4) {{
    throw new Error("adapterScenarios is missing or too short");
  }}

  const adapterScenarioIds = new Set(payload.adapterScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of [
    "adapter-file-import-preview",
    "adapter-file-import-execute",
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
    "retry_scheduled",
    "review_card",
    "manual_retry_endpoint",
  ]) {{
    if (!adapterOutputs.has(requiredOutput)) {{
      throw new Error(`adapterScenarios does not include required output: ${{requiredOutput}}`);
    }}
  }}

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
  const adapterPlan = buildAdapterOperationPlan(payload, "adapter-file-import-preview");
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${{payload.workflow.currentStage}}`,
    `adapterPlan=${{adapterPlan.phase}}`,
    `operation=${{OPERATION_ID}}`,
  );
}}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {{
  main().catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
}}
'''


def render_typescript_defs(operation_id: str, required_fields: list[str]) -> str:
    required_union = " | ".join(f'"{field}"' for field in required_fields)
    return f'''// Generated from DriveDesk Core OpenAPI. Do not edit by hand.
export const PUBLIC_DEMO_PATH: "{PUBLIC_DEMO_PATH}";
export const OPERATION_ID: "{operation_id}";
export const REQUIRED_FIELDS: Array<{required_union}>;

export type AdapterScenarioPhase = "preview" | "execute" | "retry" | "operator_review";

export interface AdapterScenario {{
  id: string;
  title: string;
  adapter: "file.import.fake" | "accounting.export.mock" | string;
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
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
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
'''


def render_readme(operation_id: str) -> str:
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

These helpers turn the public `adapterScenarios` payload into a typed
contract-only request/response plan for mapping preview, execution, retry, and
operator-review flows. They do not mutate the public demo.

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
'''


def render_manifest(operation_id: str, required_fields: list[str]) -> str:
    payload = {
        "schema_version": 1,
        "source": "docs/openapi.json",
        "path": PUBLIC_DEMO_PATH,
        "method": PUBLIC_DEMO_METHOD.upper(),
        "operation_id": operation_id,
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

    write(out_dir / "README.md", render_readme(operation_id))
    write(out_dir / "openapi-client-manifest.json", render_manifest(operation_id, required_fields))
    write(out_dir / "python/drivedesk_public_demo_client.py", render_python_client(operation_id, required_fields))
    write(out_dir / "javascript/drivedesk-public-demo-client.mjs", render_javascript_client(operation_id, required_fields))
    write(out_dir / "typescript/drivedesk-public-demo-client.d.ts", render_typescript_defs(operation_id, required_fields))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public demo clients from DriveDesk OpenAPI.")
    parser.add_argument("--openapi", type=Path, default=Path("docs/openapi.json"))
    parser.add_argument("--out", type=Path, default=Path("sdk/generated/public-demo"))
    args = parser.parse_args()

    generate(args.openapi, args.out)
    print(f"generated public demo SDK: {args.out}")


if __name__ == "__main__":
    main()
