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
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
doc_path = root / "docs/public/CONNECTOR_CERTIFICATION.md"
evidence_path = root / "docs/public/evidence/connector-certification.sanitized.json"
docs_readme_path = root / "docs/public/README.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
provider_guide_path = root / "docs/public/PROVIDER_CONNECTOR_GUIDE.md"
adapter_guide_path = root / "docs/public/ADAPTER_DEVELOPER_GUIDE.md"
adapter_catalog_path = root / "docs/public/INTEGRATION_ADAPTER_CATALOG.md"
operation_contracts_path = root / "docs/public/INTEGRATION_OPERATION_CONTRACTS.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
api_demo_path = root / "docs/public/API_BACKED_DEMO.md"
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
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
export_script_path = root / "scripts/export_public_repo.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
manifest_path = root / "PUBLIC_EXPORT_MANIFEST.md"
adr_path = root / "docs/adr/0074-public-safe-connector-certification.md"
is_public_export = manifest_path.is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(doc_path.is_file(), "missing docs/public/CONNECTOR_CERTIFICATION.md")
require(evidence_path.is_file(), "missing connector certification evidence JSON")
require(adr_path.is_file(), "missing connector certification ADR")

doc = read(doc_path)
for token in [
    "Connector Certification Path",
    "provider profile",
    "capability manifest",
    "contract fixtures",
    "local certification gate",
    "runtime readiness review",
    "release proof",
    "GET /integration-adapters",
    "operation_contracts",
    "auth_profile",
    "server_secret_store",
    "private_connector_only",
    "no_browser_token_storage",
    "contract_only",
    "safe_payload_present=true",
    "redaction_evidence_present=true",
    "proposed",
    "profile_ready",
    "manifest_ready",
    "fixtures_ready",
    "public_gate_passed",
    "private_connector_ready",
    "production_review_required",
    "drivedesk_integration_connection_checks",
    "drivedesk_integration_reconciliations",
    "drivedesk_integration_incidents",
    "integration.operator_review.created",
    "crm_deal_intake_preview",
    "crm_deal_ingest_execute",
    "accounting_export_execute",
    "file_import_preview",
    "bash scripts/check_public_connector_certification.sh",
    "bash scripts/public_repo_release_gate.sh",
]:
    require(token in doc, f"connector certification doc missing {token}")

payload = json.loads(read(evidence_path) or "{}")
require(payload.get("schema_version") == 1, "unexpected connector evidence schema version")
require(payload.get("artifact_id") == "drivedesk-core-connector-certification", "unexpected connector evidence id")
require(payload.get("status") == "validated", "connector evidence status is not validated")
require(payload.get("data_profile") == "synthetic_demo_data", "connector evidence data profile is not synthetic")
require(payload.get("public_doc") == "docs/public/CONNECTOR_CERTIFICATION.md", "connector evidence public doc mismatch")
require(payload.get("verifier") == "bash scripts/check_public_connector_certification.sh", "connector evidence verifier mismatch")

sys.path.insert(0, str(root / "apps/api"))
sys.path.insert(0, str(root / "apps/worker"))
sys.path.insert(0, str(root / "packages/core"))
from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

demo_payload = build_public_demo_payload()
certification = demo_payload.get("connectorCertification", {})
require(isinstance(certification, dict), "public demo missing connectorCertification")
require(certification.get("status") == "validated", "connectorCertification status mismatch")
require(
    certification.get("command") == "GET /demo/connector-certification",
    "connectorCertification command mismatch",
)
require(
    certification.get("certificationLevel") == "public_contract_certified",
    "connectorCertification level mismatch",
)
require(certification.get("adapterCount", 0) >= 3, "connectorCertification adapter count too low")
require(certification.get("privateReadyCount", 0) >= 2, "connectorCertification private-ready count too low")
provider_profiles = {
    item.get("adapterKey"): item
    for item in certification.get("providerProfiles", [])
    if isinstance(item, dict)
}
for adapter_key in ["crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"]:
    require(adapter_key in provider_profiles, f"connectorCertification missing provider profile: {adapter_key}")
require(
    provider_profiles.get("crm.bitrix24.mock", {}).get("readyForPrivateConnector") is True,
    "CRM connector profile should be private-ready",
)
require(
    provider_profiles.get("accounting.export.mock", {}).get("readyForPrivateConnector") is True,
    "accounting connector profile should be private-ready",
)
require(
    {item.get("stage") for item in certification.get("certificationStages", []) if isinstance(item, dict)}
    >= {
        "provider_profile",
        "capability_manifest",
        "auth_boundary",
        "fixture_replay",
        "runtime_preview",
        "execution_timeline",
        "release_gate",
    },
    "connectorCertification stage set is incomplete",
)
require(
    {item.get("gate") for item in certification.get("certificationGates", []) if isinstance(item, dict)}
    == {
        "no_real_provider_call",
        "no_secret_value",
        "no_raw_payload",
        "idempotent_execution",
        "operator_review",
    },
    "connectorCertification gate set mismatch",
)
require(
    {item.get("externalMutation") for item in certification.get("certificationGates", []) if isinstance(item, dict)}
    == {False},
    "connectorCertification gates must not mutate external providers",
)
require(
    {item.get("name") for item in certification.get("dataBoundaries", []) if isinstance(item, dict)}
    == {"public_demo_data", "browser_boundary", "private_connector_boundary"},
    "connectorCertification boundary set mismatch",
)
require(
    certification.get("api", {}).get("standalone") == "GET /demo/connector-certification",
    "connectorCertification standalone API mismatch",
)

openapi_live = build_app().openapi()
require("/demo/connector-certification" in openapi_live.get("paths", {}), "live OpenAPI missing connector certification endpoint")
required_fields = (
    openapi_live.get("components", {})
    .get("schemas", {})
    .get("PublicDemoRead", {})
    .get("required", [])
)
require("connectorCertification" in required_fields, "PublicDemoRead missing connectorCertification")

redaction = payload.get("redaction", {})
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
]:
    require(redaction.get(key) is False, f"connector evidence redaction flag must be false: {key}")

profiles = payload.get("provider_profiles", [])
require(isinstance(profiles, list) and len(profiles) >= 3, "expected at least three provider profiles")
profile_classes = {profile.get("provider_class") for profile in profiles if isinstance(profile, dict)}
for provider_class in ["crm", "bank", "accounting_or_erp"]:
    require(provider_class in profile_classes, f"missing provider profile class: {provider_class}")

stages = payload.get("certification_stages", [])
stage_keys = [stage.get("key") for stage in stages if isinstance(stage, dict)]
for stage in [
    "provider_profile",
    "capability_manifest",
    "contract_fixtures",
    "local_certification_gate",
    "runtime_readiness_review",
    "release_proof",
]:
    require(stage in stage_keys, f"missing connector certification stage: {stage}")

state_machine = payload.get("state_machine", [])
for state in [
    "proposed",
    "profile_ready",
    "manifest_ready",
    "fixtures_ready",
    "public_gate_passed",
    "private_connector_ready",
    "production_review_required",
]:
    require(state in state_machine, f"missing connector state: {state}")

fixtures = payload.get("required_fixture_groups", [])
for fixture in [
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
]:
    require(fixture in fixtures, f"missing connector fixture group: {fixture}")

fixture_assertions = payload.get("public_fixture_assertions", {})
for key in [
    "raw_payload_returned",
    "credentials_returned",
    "external_call_made",
    "public_demo_persistence",
]:
    require(fixture_assertions.get(key) is False, f"public fixture assertion must be false: {key}")
for key in ["safe_payload_present", "redaction_evidence_present"]:
    require(fixture_assertions.get(key) is True, f"public fixture assertion must be true: {key}")

runtime_surfaces = payload.get("runtime_surfaces", [])
for surface in [
    "auth_profile",
    "server_secret_store",
    "operation_contracts",
    "outbox",
    "worker",
    "drivedesk_integration_connection_checks",
    "drivedesk_integration_reconciliations",
    "drivedesk_integration_incidents",
    "integration.operator_review.created",
    "EVIDENCE_INDEX.md",
]:
    require(surface in runtime_surfaces, f"missing runtime surface: {surface}")

serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
private_patterns = [
    re.compile(r"auto\s*school\s*54", re.IGNORECASE),
    re.compile("auto" + "school54", re.IGNORECASE),
    re.compile("land" + "vps", re.IGNORECASE),
    re.compile("duck" + "dns", re.IGNORECASE),
    re.compile("xr" + "ay", re.IGNORECASE),
    re.compile("vl" + "ess", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
]
for pattern in private_patterns:
    require(not pattern.search(serialized), f"connector evidence contains private marker: {pattern.pattern}")

for path, label in [
    (docs_readme_path, "docs/public README"),
    (status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_map_path, "technical capability map"),
    (evidence_index_path, "evidence index doc"),
    (provider_guide_path, "provider connector guide"),
    (adapter_guide_path, "adapter developer guide"),
    (adapter_catalog_path, "adapter catalog"),
    (operation_contracts_path, "operation contracts"),
    (platform_tour_path, "platform tour"),
    (api_demo_path, "API-backed demo docs"),
]:
    text = read(path)
    require("CONNECTOR_CERTIFICATION.md" in text, f"{label} missing connector certification link")

for path, label, tokens in [
    (
        demo_api_path,
        "demo API",
        ["connectorCertification", "_public_connector_certification", "GET /demo/connector-certification"],
    ),
    (
        schemas_path,
        "schemas",
        ["ConnectorCertificationRead", "connectorCertification"],
    ),
    (
        main_path,
        "main API",
        ["/demo/connector-certification", "ConnectorCertificationRead"],
    ),
    (
        demo_app_path,
        "public demo app",
        [
            "connectorCertification",
            "fillConnectorCertification",
            "connectorCertificationProviderRows",
        ],
    ),
    (
        demo_html_path,
        "public demo HTML",
        [
            "Connector Certification",
            "connectorCertificationSummaryRows",
            "connectorCertificationGateRows",
        ],
    ),
    (
        openapi_path,
        "committed OpenAPI",
        ["/demo/connector-certification", "ConnectorCertificationRead", "connectorCertification"],
    ),
    (
        sdk_manifest_path,
        "SDK manifest",
        ["connector_certification", "/demo/connector-certification", "connectorCertification"],
    ),
    (
        sdk_python_path,
        "Python SDK",
        ["get_connector_certification", "validate_connector_certification_payload"],
    ),
    (
        sdk_javascript_path,
        "JavaScript SDK",
        ["getConnectorCertification", "validateConnectorCertificationPayload"],
    ),
    (
        sdk_typescript_path,
        "TypeScript SDK",
        ["ConnectorCertificationPayload", "getConnectorCertification"],
    ),
]:
    text = read(path)
    for token in tokens:
        require(token in text, f"{label} missing connector certification token: {token}")

evidence_index_payload = json.loads(read(evidence_index_json_path) or "{}")
entries = evidence_index_payload.get("entries", [])
connector_entries = [
    entry for entry in entries
    if isinstance(entry, dict) and entry.get("capability_id") == "connector-certification"
]
require(len(connector_entries) == 1, "evidence index missing connector-certification entry")
if connector_entries:
    entry = connector_entries[0]
    require(entry.get("public_doc") == "docs/public/CONNECTOR_CERTIFICATION.md", "connector evidence index public doc mismatch")
    require(
        "docs/public/evidence/connector-certification.sanitized.json" in entry.get("evidence_files", []),
        "connector evidence index missing evidence file",
    )
    require(
        "bash scripts/check_public_connector_certification.sh" in entry.get("verifiers", []),
        "connector evidence index missing verifier",
    )

if is_public_export:
    public_smoke = read(public_smoke_path)
    require("CONNECTOR_CERTIFICATION.md" in read(root_readme_path), "public README missing connector certification")
    require("docs/public/CONNECTOR_CERTIFICATION.md" in read(index_html_path), "public Pages root missing connector certification")
    require("check_public_connector_certification.sh" in public_smoke, "public smoke missing connector certification check")
    require("public connector certification doc" in read(manifest_path), "public manifest missing connector certification")
else:
    export_script = read(export_script_path)
    private_smoke = read(private_smoke_path)
    release_gate = read(release_gate_path)
    require('copy_path "scripts/check_public_connector_certification.sh"' in export_script, "export script missing connector checker copy")
    require("CONNECTOR_CERTIFICATION.md" in export_script, "export script missing connector certification references")
    require("connector-certification.sanitized.json" in export_script, "export script missing connector evidence reference")
    require("public connector certification doc" in export_script, "export manifest missing connector certification")
    require("check_public_connector_certification.sh" in private_smoke, "private smoke missing connector certification check")
    require("docs/public/CONNECTOR_CERTIFICATION.md" in release_gate, "release gate missing connector certification required file")
    require("docs/public/evidence/connector-certification.sanitized.json" in release_gate, "release gate missing connector evidence required file")
    require("scripts/check_public_connector_certification.sh" in release_gate, "release gate missing connector checker required file")
    require("missing connector certification" in release_gate, "release gate missing connector certification errors")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public connector certification check ok")
PY
