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
doc_path = root / "docs/public/PROVIDER_ONBOARDING.md"
evidence_path = root / "docs/public/evidence/provider-onboarding.sanitized.json"
demo_api_path = root / "apps/api/drivedesk_api/demo.py"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
openapi_path = root / "docs/openapi.json"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
sdk_python_path = root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py"
sdk_javascript_path = root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs"
sdk_typescript_path = root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts"
docs_readme_path = root / "docs/public/README.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
api_docs_path = root / "docs/public/API_BACKED_DEMO.md"
client_sdk_path = root / "docs/public/CLIENT_SDK.md"
export_script_path = root / "scripts/export_public_repo.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
manifest_path = root / "PUBLIC_EXPORT_MANIFEST.md"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
is_public_export = manifest_path.is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(doc_path.is_file(), "missing docs/public/PROVIDER_ONBOARDING.md")
require(evidence_path.is_file(), "missing provider onboarding evidence JSON")

doc = read(doc_path)
for token in [
    "Provider Onboarding Workbench",
    "GET /demo/provider-onboarding",
    "providerProfile",
    "onboardingStages",
    "mappingPreview",
    "preflightChecks",
    "sandboxContract",
    "rolloutPlan",
    "select_provider_profile",
    "bind_connection_profile",
    "mapping_preview",
    "sandbox_dry_run",
    "approval_review",
    "private_rollout",
    "crm.bitrix24.mock",
    "crm_deal_intake_preview",
    "crm_deal_ingest_execute",
    "providerCallEnabled=false",
    "externalMutation=false",
    "private_connector_only",
    "bash scripts/check_public_provider_onboarding.sh",
]:
    require(token in doc, f"provider onboarding doc missing {token}")

evidence = json.loads(read(evidence_path) or "{}")
require(evidence.get("schema_version") == 1, "unexpected provider onboarding evidence schema")
require(evidence.get("artifact_id") == "drivedesk-core-provider-onboarding", "unexpected provider onboarding evidence id")
require(evidence.get("status") == "previewed", "unexpected provider onboarding evidence status")
require(evidence.get("provider_key") == "crm.bitrix24.mock", "unexpected provider onboarding evidence provider")
require(evidence.get("onboarding_level") == "sandbox_onboarding_ready", "unexpected provider onboarding evidence level")
require(evidence.get("verifier") == "bash scripts/check_public_provider_onboarding.sh", "provider onboarding evidence verifier mismatch")
for stage in [
    "select_provider_profile",
    "bind_connection_profile",
    "mapping_preview",
    "sandbox_dry_run",
    "approval_review",
    "private_rollout",
]:
    require(stage in evidence.get("onboarding_stages", []), f"provider onboarding evidence missing stage: {stage}")
for key in [
    "provider_call_enabled",
    "external_mutation",
    "raw_payload_included",
    "contains_pii",
    "browser_token_storage",
    "public_demo_persistence",
]:
    require(evidence.get("safety_assertions", {}).get(key) is False, f"provider onboarding safety assertion must be false: {key}")
for key in [
    "server_secret_store",
    "private_connector_only",
    "tenant_scoped_connection_profile",
    "mapping_preview",
    "fixture_replay",
    "sandbox_dry_run",
    "approval_gateway",
    "idempotency_keys",
    "reconciliation",
    "scheduled_validation",
]:
    require(key in evidence.get("private_rollout_requirements", []), f"provider onboarding evidence missing rollout requirement: {key}")
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
]:
    require(evidence.get("redaction", {}).get(key) is False, f"provider onboarding redaction flag must be false: {key}")

sys.path.insert(0, str(root / "apps/api"))
sys.path.insert(0, str(root / "apps/worker"))
sys.path.insert(0, str(root / "packages/core"))
from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

demo = build_public_demo_payload()
onboarding = demo.get("providerOnboarding", {})
require(isinstance(onboarding, dict), "public demo missing providerOnboarding")
require(onboarding.get("status") == "previewed", "providerOnboarding status mismatch")
require(onboarding.get("command") == "GET /demo/provider-onboarding", "providerOnboarding command mismatch")
require(onboarding.get("onboardingLevel") == "sandbox_onboarding_ready", "providerOnboarding level mismatch")
require(onboarding.get("providerKey") == "crm.bitrix24.mock", "providerOnboarding provider mismatch")
require(onboarding.get("providerProfile", {}).get("adapterKey") == "crm.bitrix24.mock", "providerOnboarding profile key mismatch")
require(onboarding.get("providerProfile", {}).get("publicDemoRequiresSecret") is False, "providerOnboarding public secret flag mismatch")
require(onboarding.get("providerProfile", {}).get("realProviderRequiresSecret") is True, "providerOnboarding real secret flag mismatch")
require(
    {"crm_deal_intake_preview", "crm_deal_ingest_execute"}.issubset(
        set(onboarding.get("providerProfile", {}).get("operationKeys", []))
    ),
    "providerOnboarding operation keys incomplete",
)
require(
    {item.get("stage") for item in onboarding.get("onboardingStages", []) if isinstance(item, dict)}
    >= {
        "select_provider_profile",
        "bind_connection_profile",
        "mapping_preview",
        "sandbox_dry_run",
        "approval_review",
        "private_rollout",
    },
    "providerOnboarding stage set incomplete",
)
mapping_preview = onboarding.get("mappingPreview", {})
require(mapping_preview.get("recordsAccepted") == 2, "providerOnboarding mapping accepted count mismatch")
require(mapping_preview.get("recordsRejected") == 0, "providerOnboarding mapping rejected count mismatch")
require(mapping_preview.get("rawPayloadIncluded") is False, "providerOnboarding mapping must not expose raw payload")
require(mapping_preview.get("containsPii") is False, "providerOnboarding mapping must not expose PII")
require(
    {"ACCESS_TOKEN", "CLIENT_NAME", "EMAIL", "PHONE", "SECRET"}.issubset(
        set(mapping_preview.get("droppedSensitiveKeys", []))
    ),
    "providerOnboarding dropped sensitive keys incomplete",
)
require(
    {item.get("check") for item in onboarding.get("preflightChecks", []) if isinstance(item, dict)}
    >= {
        "adapter_registered",
        "connection_scopes_available",
        "mapping_profile_valid",
        "secret_refs_server_side",
        "provider_call_disabled",
    },
    "providerOnboarding preflight checks incomplete",
)
require(
    {item.get("externalMutation") for item in onboarding.get("preflightChecks", []) if isinstance(item, dict)}
    == {False},
    "providerOnboarding preflight must not mutate providers",
)
sandbox = onboarding.get("sandboxContract", {})
require(sandbox.get("previewOperation") == "crm_deal_intake_preview", "providerOnboarding preview operation mismatch")
require(sandbox.get("executeOperation") == "crm_deal_ingest_execute", "providerOnboarding execute operation mismatch")
require(sandbox.get("providerCallEnabled") is False, "providerOnboarding sandbox provider call must be false")
require(sandbox.get("externalMutation") is False, "providerOnboarding sandbox mutation must be false")
require(
    {item.get("step") for item in onboarding.get("rolloutPlan", []) if isinstance(item, dict)}
    >= {
        "create_tenant_connection",
        "run_mapping_preview",
        "run_fixture_replay",
        "enable_private_dry_run",
        "request_write_unlock",
        "monitor_and_reconcile",
    },
    "providerOnboarding rollout plan incomplete",
)
require(
    {item.get("name") for item in onboarding.get("dataBoundaries", []) if isinstance(item, dict)}
    == {
        "public_onboarding_payload",
        "server_secret_store",
        "browser_session",
        "private_provider_runtime",
    },
    "providerOnboarding data boundary set mismatch",
)
require(
    {item.get("externalMutation") for item in onboarding.get("dataBoundaries", []) if isinstance(item, dict)}
    == {False},
    "providerOnboarding data boundaries must not mutate providers",
)
require(onboarding.get("api", {}).get("standalone") == "GET /demo/provider-onboarding", "providerOnboarding standalone API mismatch")

openapi_live = build_app().openapi()
require("/demo/provider-onboarding" in openapi_live.get("paths", {}), "live OpenAPI missing provider onboarding endpoint")
required_fields = (
    openapi_live.get("components", {})
    .get("schemas", {})
    .get("PublicDemoRead", {})
    .get("required", [])
)
require("providerOnboarding" in required_fields, "PublicDemoRead missing providerOnboarding")
require("ProviderOnboardingRead" in openapi_live.get("components", {}).get("schemas", {}), "OpenAPI missing ProviderOnboardingRead")

for path, label, tokens in [
    (
        demo_api_path,
        "demo API",
        ["providerOnboarding", "_public_provider_onboarding", "GET /demo/provider-onboarding"],
    ),
    (
        schemas_path,
        "schemas",
        ["ProviderOnboardingRead", "providerOnboarding"],
    ),
    (
        main_path,
        "main API",
        ["/demo/provider-onboarding", "ProviderOnboardingRead"],
    ),
    (
        demo_app_path,
        "public demo app",
        ["providerOnboarding", "fillProviderOnboarding", "providerOnboardingStageRows"],
    ),
    (
        demo_html_path,
        "public demo HTML",
        ["Provider Onboarding", "providerOnboardingSummaryRows", "providerOnboardingRolloutRows"],
    ),
    (
        openapi_path,
        "committed OpenAPI",
        ["/demo/provider-onboarding", "ProviderOnboardingRead", "providerOnboarding"],
    ),
    (
        sdk_manifest_path,
        "SDK manifest",
        ["provider_onboarding", "/demo/provider-onboarding", "providerOnboarding"],
    ),
    (
        sdk_python_path,
        "Python SDK",
        ["get_provider_onboarding", "validate_provider_onboarding_payload"],
    ),
    (
        sdk_javascript_path,
        "JavaScript SDK",
        ["getProviderOnboarding", "validateProviderOnboardingPayload"],
    ),
    (
        sdk_typescript_path,
        "TypeScript SDK",
        ["ProviderOnboardingPayload", "getProviderOnboarding"],
    ),
]:
    text = read(path)
    for token in tokens:
        require(token in text, f"{label} missing provider onboarding token: {token}")

for path, label in [
    (docs_readme_path, "docs/public README"),
    (status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_path, "technical capability map"),
    (api_docs_path, "API-backed demo docs"),
    (client_sdk_path, "client SDK docs"),
]:
    require("PROVIDER_ONBOARDING.md" in read(path), f"{label} missing provider onboarding link")

if is_public_export:
    require("PROVIDER_ONBOARDING.md" in read(root_readme_path), "public README missing provider onboarding")
    require("docs/public/PROVIDER_ONBOARDING.md" in read(index_html_path), "public Pages root missing provider onboarding")
    require("check_public_provider_onboarding.sh" in read(public_smoke_path), "public smoke missing provider onboarding check")
    require("public provider onboarding doc" in read(manifest_path), "public manifest missing provider onboarding")
else:
    require('copy_path "scripts/check_public_provider_onboarding.sh"' in read(export_script_path), "export script missing provider onboarding checker copy")
    require("PROVIDER_ONBOARDING.md" in read(export_script_path), "export script missing provider onboarding references")
    require("provider-onboarding.sanitized.json" in read(export_script_path), "export script missing provider onboarding evidence")
    require("check_public_provider_onboarding.sh" in read(private_smoke_path), "private smoke missing provider onboarding check")
    require("docs/public/PROVIDER_ONBOARDING.md" in read(release_gate_path), "release gate missing provider onboarding doc")
    require("scripts/check_public_provider_onboarding.sh" in read(release_gate_path), "release gate missing provider onboarding checker")
    require("missing provider onboarding" in read(release_gate_path), "release gate missing provider onboarding error")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public provider onboarding check ok")
PY
