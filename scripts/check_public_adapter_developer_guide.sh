#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$ROOT"

if [[ -n "${DRIVEDESK_PYTHON:-}" && -x "$DRIVEDESK_PYTHON" ]]; then
  PYTHON_BIN="$DRIVEDESK_PYTHON"
elif [[ -n "${PUBLIC_EXPORT_PYTHON:-}" && -x "$PUBLIC_EXPORT_PYTHON" ]]; then
  PYTHON_BIN="$PUBLIC_EXPORT_PYTHON"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python is required" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY' "$ROOT"
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
guide_path = root / "docs/public/ADAPTER_DEVELOPER_GUIDE.md"
readme_path = root / "docs/public/README.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
client_sdk_path = root / "docs/public/CLIENT_SDK.md"
provider_guide_path = root / "docs/public/PROVIDER_CONNECTOR_GUIDE.md"
generator_path = root / "scripts/generate_public_demo_sdk.py"
python_example_path = root / "examples/python/demo_adapter_operation_plan.py"
js_example_path = root / "examples/js/demo-adapter-operation-plan.mjs"
manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
python_client_path = root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py"
js_client_path = root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs"
ts_defs_path = root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
export_script_path = root / "scripts/export_public_repo.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(guide_path.is_file(), "missing docs/public/ADAPTER_DEVELOPER_GUIDE.md")
guide = read(guide_path)

for token in [
    "Adapter Developer Guide",
    "GET /demo/public",
    "adapterScenarios",
    "generated SDK operation plan",
    "build_adapter_operation_plan",
    "buildAdapterOperationPlan",
    "adapter-crm-deal-preview",
    "adapter-crm-deal-ingest",
    "crm_deal_intake_preview",
    "crm_deal_ingest_execute",
    "WORKER worker:drivedesk_worker.main.process_pending_outbox",
    "POST /tenants/{tenant_id}/business-provider-intake/preview",
    "safe_payload",
    "normalized_observation",
    "no_provider_call",
    "integration.crm_deal.ingest.requested",
    "idempotency key",
    "outbox event",
    "retry",
    "dead-letter",
    "operator_review",
    "auth_profile",
    "oauth2_or_webhook_boundary",
    "server_secret_store",
    "private_connector_only",
    "no_browser_token_storage",
    "drivedesk_integration_connection_checks",
    "drivedesk_integration_reconciliations",
    "drivedesk_integration_incidents",
    "check_public_adapter_developer_guide.sh",
    "check_public_demo_sdk.sh",
    "check_public_provider_connector_guide.sh",
]:
    require(token in guide, f"adapter developer guide missing {token}")

for path, label in [
    (readme_path, "docs/public README"),
    (status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_map_path, "technical capability map"),
    (client_sdk_path, "client SDK docs"),
    (provider_guide_path, "provider connector guide"),
]:
    require("ADAPTER_DEVELOPER_GUIDE.md" in read(path), f"{label} missing adapter developer guide link")

for path, label in [
    (generator_path, "SDK generator"),
    (python_example_path, "Python adapter operation example"),
    (js_example_path, "JavaScript adapter operation example"),
    (python_client_path, "generated Python SDK"),
    (js_client_path, "generated JavaScript SDK"),
]:
    text = read(path)
    require("adapter-crm-deal-preview" in text, f"{label} missing CRM preview scenario")
    require("crm_deal_intake_preview" in text, f"{label} missing CRM preview operation")
    require("crm.bitrix24.mock" in text, f"{label} missing CRM adapter key")
    require("provider_payload" in text, f"{label} missing provider payload plan")

for path, label in [
    (generator_path, "SDK generator"),
    (python_client_path, "generated Python SDK"),
    (js_client_path, "generated JavaScript SDK"),
    (ts_defs_path, "generated TypeScript definitions"),
]:
    require("WORKER" in read(path), f"{label} missing WORKER endpoint support")

manifest = json.loads(read(manifest_path) or "{}")
scenarios = manifest.get("adapter_helper_scenarios", [])
for scenario_id in [
    "adapter-file-import-preview",
    "adapter-file-import-execute",
    "adapter-crm-deal-preview",
    "adapter-crm-deal-ingest",
    "adapter-accounting-export-retry",
    "adapter-dead-letter-review",
]:
    require(scenario_id in scenarios, f"SDK manifest missing {scenario_id}")

if is_public_export:
    require(public_smoke_path.is_file(), "public smoke missing in public export")
    require(
        "check_public_adapter_developer_guide.sh" in read(public_smoke_path),
        "public smoke missing adapter developer guide check",
    )
else:
    release_gate = read(release_gate_path)
    export_script = read(export_script_path)
    require("docs/public/ADAPTER_DEVELOPER_GUIDE.md" in release_gate, "release gate missing adapter developer guide file check")
    require("missing adapter developer guide" in release_gate, "release gate missing adapter developer guide error")
    require("check_public_adapter_developer_guide.sh" in release_gate, "release gate missing adapter developer guide script check")
    require('copy_path "scripts/check_public_adapter_developer_guide.sh"' in export_script, "export script missing adapter developer guide checker")
    require("public adapter developer guide" in export_script, "export manifest missing adapter developer guide")
    require("check_public_adapter_developer_guide.sh" in read(private_smoke_path), "private smoke missing adapter developer guide check")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public adapter developer guide check ok")
PY
