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

    def _get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{{self.base_url}}{{path}}",
            headers={{"Accept": "application/json", "User-Agent": "drivedesk-public-demo-sdk/1"}},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


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
    print(
        "generated python SDK ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={{payload['workflow']['currentStage']}}",
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
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${{payload.workflow.currentStage}}`,
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
  timeline: Array<Record<string, string>>;
  domainEvents: Array<Record<string, string>>;
}}

export class DriveDeskPublicDemoClient {{
  constructor(baseUrl?: string, options?: {{ fetchImpl?: typeof fetch }});
  getPublicDemo(): Promise<PublicDemoPayload>;
}}

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
        "data_profile": "synthetic_fake_data",
        "generated_files": [
            "README.md",
            "openapi-client-manifest.json",
            "python/drivedesk_public_demo_client.py",
            "javascript/drivedesk-public-demo-client.mjs",
            "typescript/drivedesk-public-demo-client.d.ts",
        ],
        "required_fields": required_fields,
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
