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
doc_path = root / "docs/public/CONNECTOR_FIXTURE_REPLAY.md"
evidence_path = root / "docs/public/evidence/connector-fixture-replay.sanitized.json"
fixture_path = root / "examples/connector-fixtures/replay-fixtures.sanitized.json"
certification_path = root / "docs/public/CONNECTOR_CERTIFICATION.md"
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
api_demo_payload_path = root / "apps/api/drivedesk_api/demo.py"
api_schema_path = root / "apps/api/drivedesk_api/schemas.py"
api_main_path = root / "apps/api/drivedesk_api/main.py"
public_demo_html_path = root / "apps/admin/public-demo/index.html"
public_demo_js_path = root / "apps/admin/public-demo/app.js"
public_demo_data_path = root / "apps/admin/public-demo/demo-data.js"
public_demo_api_check_path = root / "scripts/check_public_demo_api.sh"
sdk_generator_path = root / "scripts/generate_public_demo_sdk.py"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
sdk_python_path = root / "sdk/generated/public-demo/python/drivedesk_public_demo_client.py"
sdk_js_path = root / "sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs"
sdk_types_path = root / "sdk/generated/public-demo/typescript/drivedesk-public-demo-client.d.ts"
root_readme_path = root / "README.md"
index_html_path = root / "index.html"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
export_script_path = root / "scripts/export_public_repo.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
manifest_path = root / "PUBLIC_EXPORT_MANIFEST.md"
adr_path = root / "docs/adr/0075-public-safe-connector-fixture-replay.md"
is_public_export = manifest_path.is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(doc_path.is_file(), "missing docs/public/CONNECTOR_FIXTURE_REPLAY.md")
require(evidence_path.is_file(), "missing connector fixture replay evidence JSON")
require(fixture_path.is_file(), "missing connector replay fixture JSON")
require(adr_path.is_file(), "missing connector fixture replay ADR")

doc = read(doc_path)
for token in [
    "Connector Fixture Replay",
    "CONNECTOR_CERTIFICATION.md",
    "examples/connector-fixtures/replay-fixtures.sanitized.json",
    "docs/public/evidence/connector-fixture-replay.sanitized.json",
    "bash scripts/check_public_connector_fixture_replay.sh",
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
    "raw_payload_returned=false",
    "credentials_returned=false",
    "external_call_made=false",
    "public_demo_persistence=false",
    "safe_payload_present=true",
    "integration.operator_review.created",
    "drivedesk_integration_reconciliations",
    "fixtures_ready",
    "public_gate_passed",
    "connectorFixtureReplay",
    "connectorReplayOutcomeRows",
]:
    require(token in doc, f"connector fixture replay doc missing {token}")

payload = json.loads(read(evidence_path) or "{}")
fixture_payload = json.loads(read(fixture_path) or "{}")

require(payload.get("schema_version") == 1, "unexpected replay evidence schema version")
require(payload.get("artifact_id") == "drivedesk-core-connector-fixture-replay", "unexpected replay evidence id")
require(payload.get("status") == "validated", "replay evidence status is not validated")
require(payload.get("data_profile") == "synthetic_demo_data", "replay evidence data profile is not synthetic")
require(payload.get("public_doc") == "docs/public/CONNECTOR_FIXTURE_REPLAY.md", "replay evidence public doc mismatch")
require(payload.get("fixture_file") == "examples/connector-fixtures/replay-fixtures.sanitized.json", "replay evidence fixture file mismatch")
require(payload.get("certification_doc") == "docs/public/CONNECTOR_CERTIFICATION.md", "replay evidence certification doc mismatch")
require(payload.get("verifier") == "bash scripts/check_public_connector_fixture_replay.sh", "replay evidence verifier mismatch")

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
    require(redaction.get(key) is False, f"replay evidence redaction flag must be false: {key}")

for stage in [
    "load_fixture",
    "validate_contract",
    "normalize_safe_payload",
    "redact_sensitive_fields",
    "classify_outcome",
    "route_followup",
    "record_sanitized_evidence",
]:
    require(stage in payload.get("replay_stages", []), f"missing replay stage: {stage}")

required_groups = [
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
]

evidence_fixtures = payload.get("fixture_groups", [])
fixture_file_fixtures = fixture_payload.get("fixtures", [])
require(isinstance(evidence_fixtures, list), "evidence fixture_groups must be a list")
require(isinstance(fixture_file_fixtures, list), "fixture file fixtures must be a list")

evidence_by_group = {
    item.get("group"): item
    for item in evidence_fixtures
    if isinstance(item, dict)
}
fixture_file_by_group = {
    item.get("group"): item
    for item in fixture_file_fixtures
    if isinstance(item, dict)
}

require(set(evidence_by_group) == set(required_groups), "evidence fixture groups do not match required groups")
require(set(fixture_file_by_group) == set(required_groups), "fixture file groups do not match required groups")
require(fixture_payload.get("schema_version") == 1, "unexpected replay fixture schema version")
require(
    fixture_payload.get("fixture_set_id") == "drivedesk-core-connector-fixture-replay-fixtures",
    "unexpected replay fixture set id",
)
require(fixture_payload.get("data_profile") == "synthetic_demo_data", "fixture file data profile is not synthetic")
require(fixture_payload.get("public_doc") == "docs/public/CONNECTOR_FIXTURE_REPLAY.md", "fixture file public doc mismatch")
require(
    fixture_payload.get("expected_replay_command") == "bash scripts/check_public_connector_fixture_replay.sh",
    "fixture file replay command mismatch",
)

for group in required_groups:
    evidence_fixture = evidence_by_group.get(group, {})
    fixture_file_fixture = fixture_file_by_group.get(group, {})
    for key in ["provider_key", "provider_class", "stage", "input_profile", "expected_result"]:
        require(key in evidence_fixture, f"{group} evidence fixture missing {key}")
        require(key in fixture_file_fixture, f"{group} fixture file missing {key}")
    require(
        evidence_fixture.get("provider_key") == fixture_file_fixture.get("provider_key"),
        f"{group} provider key mismatch between evidence and fixture file",
    )
    require(
        evidence_fixture.get("provider_class") == fixture_file_fixture.get("provider_class"),
        f"{group} provider class mismatch between evidence and fixture file",
    )
    require(
        evidence_fixture.get("stage") == fixture_file_fixture.get("stage"),
        f"{group} stage mismatch between evidence and fixture file",
    )

    expected = evidence_fixture.get("expected_result", {})
    fixture_expected = fixture_file_fixture.get("expected_result", {})
    require(expected == fixture_expected, f"{group} expected result mismatch")
    require(expected.get("safe_payload_present") is True, f"{group} must keep safe payload present")
    for key in [
        "raw_payload_returned",
        "credentials_returned",
        "external_call_made",
        "public_demo_persistence",
    ]:
        require(expected.get(key) is False, f"{group} public boundary must be false: {key}")

happy = evidence_by_group.get("happy_path_preview", {}).get("expected_result", {})
require("external_reference" in happy.get("normalized_fields", []), "happy path missing external_reference normalization")
require("amount_bucket" in happy.get("normalized_fields", []), "happy path missing amount_bucket normalization")

redaction_expected = evidence_by_group.get("sensitive_payload_redaction", {}).get("expected_result", {})
require(redaction_expected.get("redaction_evidence_present") is True, "redaction fixture missing redaction evidence")
for key in ["access_token", "refresh_token", "full_name", "phone", "email", "address", "raw_request_body"]:
    require(key in redaction_expected.get("dropped_keys", []), f"redaction fixture missing dropped key: {key}")

invalid = evidence_by_group.get("invalid_payload", {}).get("expected_result", {})
require(invalid.get("outbox_event_created") is False, "invalid payload must not create outbox work")
require(len(invalid.get("validation_errors", [])) >= 2, "invalid payload must expose validation errors")

retryable = evidence_by_group.get("retryable_provider_failure", {}).get("expected_result", {})
require(retryable.get("retryable") is True, "retryable failure must be retryable")
require(retryable.get("dead_letter") is False, "retryable failure must not dead-letter")
require(retryable.get("next_state") == "retry_scheduled", "retryable failure must schedule retry")

dead_letter = evidence_by_group.get("dead_letter_provider_failure", {}).get("expected_result", {})
require(dead_letter.get("retryable") is False, "dead-letter fixture must not be retryable")
require(dead_letter.get("dead_letter") is True, "dead-letter fixture must dead-letter")
require(dead_letter.get("operator_review") is True, "dead-letter fixture must create operator review")
require(
    dead_letter.get("event_type") == "integration.operator_review.created",
    "dead-letter fixture missing operator review event",
)
require(
    dead_letter.get("incident_table") == "drivedesk_integration_incidents",
    "dead-letter fixture missing incident table",
)

reconciliation = evidence_by_group.get("reconciliation_mismatch", {}).get("expected_result", {})
require(
    reconciliation.get("reconciliation_table") == "drivedesk_integration_reconciliations",
    "reconciliation fixture missing reconciliation table",
)
require(reconciliation.get("status") == "mismatch", "reconciliation fixture must be mismatch")
require(reconciliation.get("operator_review") is True, "reconciliation mismatch must route to operator review")

serialized = "\n".join(
    [
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        json.dumps(fixture_payload, ensure_ascii=False, sort_keys=True),
        doc,
    ]
)
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
    require(not pattern.search(serialized), f"connector replay artifact contains private marker: {pattern.pattern}")

for path, label in [
    (certification_path, "connector certification"),
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
    require("CONNECTOR_FIXTURE_REPLAY.md" in text, f"{label} missing connector fixture replay link")

for path, label, tokens in [
    (
        api_demo_payload_path,
        "public demo API payload",
        [
            "connectorFixtureReplay",
            "retryable_provider_failure",
            "dead_letter_provider_failure",
            "reconciliation_mismatch",
        ],
    ),
    (
        api_schema_path,
        "public demo API schema",
        ["ConnectorFixtureReplayRead", "connectorFixtureReplay"],
    ),
    (
        api_main_path,
        "public demo API routes",
        ["/demo/connector-fixture-replay", "connector_fixture_replay_demo"],
    ),
    (
        public_demo_data_path,
        "public demo static payload",
        [
            "connectorFixtureReplay",
            "docs/public/evidence/connector-fixture-replay.sanitized.json",
            "examples/connector-fixtures/replay-fixtures.sanitized.json",
        ],
    ),
    (
        public_demo_html_path,
        "public demo HTML",
        [
            "connectorReplaySummaryRows",
            "connectorReplayOutcomeRows",
            "connectorReplayBoundaryRows",
            "connectorReplayDocRows",
        ],
    ),
    (
        public_demo_js_path,
        "public demo renderer",
        [
            "Array.isArray(payload.connectorFixtureReplay.summary)",
            "fillConnectorFixtureReplay",
            "connectorReplayOutcomeRows",
            "connectorReplayBoundaryRows",
        ],
    ),
    (
        public_demo_api_check_path,
        "public demo API checker",
        [
            "/demo/connector-fixture-replay",
            "connectorFixtureReplay",
            "happy_path_preview",
            "safe_payload_present=true",
            "drivedesk_integration_reconciliations",
        ],
    ),
    (
        sdk_generator_path,
        "SDK generator",
        [
            "/demo/connector-fixture-replay",
            "ConnectorFixtureReplayRead",
            "get_connector_fixture_replay",
            "getConnectorFixtureReplay",
        ],
    ),
    (
        sdk_manifest_path,
        "SDK manifest",
        [
            "/demo/connector-fixture-replay",
            "connector_fixture_replay_demo_demo_connector_fixture_replay_get",
        ],
    ),
    (
        sdk_python_path,
        "Python SDK",
        ["get_connector_fixture_replay", "validate_connector_fixture_replay_payload"],
    ),
    (
        sdk_js_path,
        "JavaScript SDK",
        ["getConnectorFixtureReplay", "validateConnectorFixtureReplayPayload"],
    ),
    (
        sdk_types_path,
        "TypeScript SDK",
        ["ConnectorFixtureReplayPayload", "getConnectorFixtureReplay"],
    ),
]:
    text = read(path)
    for token in tokens:
        require(token in text, f"{label} missing {token}")

evidence_index_payload = json.loads(read(evidence_index_json_path) or "{}")
entries = evidence_index_payload.get("entries", [])
replay_entries = [
    entry for entry in entries
    if isinstance(entry, dict) and entry.get("capability_id") == "connector-fixture-replay"
]
require(len(replay_entries) == 1, "evidence index missing connector-fixture-replay entry")
if replay_entries:
    entry = replay_entries[0]
    require(entry.get("public_doc") == "docs/public/CONNECTOR_FIXTURE_REPLAY.md", "replay evidence index public doc mismatch")
    for evidence_file in [
        "docs/public/evidence/connector-fixture-replay.sanitized.json",
        "examples/connector-fixtures/replay-fixtures.sanitized.json",
    ]:
        require(evidence_file in entry.get("evidence_files", []), f"replay evidence index missing {evidence_file}")
    require(
        "bash scripts/check_public_connector_fixture_replay.sh" in entry.get("verifiers", []),
        "replay evidence index missing verifier",
    )

if is_public_export:
    public_smoke = read(public_smoke_path)
    require("CONNECTOR_FIXTURE_REPLAY.md" in read(root_readme_path), "public README missing connector fixture replay")
    require("docs/public/CONNECTOR_FIXTURE_REPLAY.md" in read(index_html_path), "public Pages root missing connector fixture replay")
    require("check_public_connector_fixture_replay.sh" in public_smoke, "public smoke missing connector fixture replay check")
    require("public connector fixture replay doc" in read(manifest_path), "public manifest missing connector fixture replay")
else:
    export_script = read(export_script_path)
    private_smoke = read(private_smoke_path)
    release_gate = read(release_gate_path)
    require('copy_path "scripts/check_public_connector_fixture_replay.sh"' in export_script, "export script missing connector fixture replay checker copy")
    require("CONNECTOR_FIXTURE_REPLAY.md" in export_script, "export script missing connector fixture replay references")
    require("connector-fixture-replay.sanitized.json" in export_script, "export script missing connector fixture replay evidence reference")
    require("examples/connector-fixtures/replay-fixtures.sanitized.json" in release_gate, "release gate missing connector replay fixture required file")
    require("public connector fixture replay doc" in export_script, "export manifest missing connector fixture replay")
    require("check_public_connector_fixture_replay.sh" in private_smoke, "private smoke missing connector fixture replay check")
    require("docs/public/CONNECTOR_FIXTURE_REPLAY.md" in release_gate, "release gate missing connector fixture replay required file")
    require("docs/public/evidence/connector-fixture-replay.sanitized.json" in release_gate, "release gate missing connector fixture replay evidence required file")
    require("scripts/check_public_connector_fixture_replay.sh" in release_gate, "release gate missing connector fixture replay checker required file")
    require("missing connector fixture replay" in release_gate, "release gate missing connector fixture replay errors")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public connector fixture replay check ok")
PY
