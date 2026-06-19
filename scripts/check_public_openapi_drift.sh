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

export PYTHONPATH="$ROOT/apps/api:$ROOT/apps/worker:$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" - <<'PY' "$ROOT"
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from drivedesk_api.main import app

root = Path(sys.argv[1])
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing json file: {path.relative_to(root)}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
doc_path = root / "docs/public/OPENAPI_DRIFT.md"
evidence_path = root / "docs/public/evidence/openapi-drift.sanitized.json"
openapi_path = root / "docs/openapi.json"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
public_demo_health_path = root / "docs/public/PUBLIC_DEMO_HEALTH.md"
docs_readme_path = root / "docs/public/README.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"

for path in [
    doc_path,
    evidence_path,
    openapi_path,
    sdk_manifest_path,
    demo_data_path,
    public_demo_health_path,
    docs_readme_path,
    evidence_index_path,
    evidence_index_json_path,
    project_status_path,
    roadmap_path,
    capability_map_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

evidence = load_json(evidence_path)
committed_openapi = load_json(openapi_path)
generated_openapi = app.openapi()
sdk_manifest = load_json(sdk_manifest_path)

require(evidence.get("schema_version") == 1, "OpenAPI drift evidence schema version mismatch")
require(evidence.get("check") == "public_openapi_drift", "OpenAPI drift evidence check mismatch")
require(evidence.get("status") == "validated", "OpenAPI drift evidence status mismatch")
require(evidence.get("data_profile") == "synthetic_demo_data", "OpenAPI drift data profile mismatch")
require(
    evidence.get("drift_model") == "fastapi_generated_openapi_to_committed_public_contract",
    "OpenAPI drift model mismatch",
)

require(
    canonical(committed_openapi) == canonical(generated_openapi),
    "docs/openapi.json does not match FastAPI app.openapi() output; regenerate public OpenAPI",
)

openapi_evidence = evidence.get("openapi", {}) if isinstance(evidence.get("openapi"), dict) else {}
paths = committed_openapi.get("paths", {}) if isinstance(committed_openapi.get("paths"), dict) else {}
schemas = (
    committed_openapi.get("components", {}).get("schemas", {})
    if isinstance(committed_openapi.get("components"), dict)
    else {}
)
openapi_hash = hashlib.sha256(canonical(committed_openapi)).hexdigest()[:16]
sdk_hash = hashlib.sha256(canonical(sdk_manifest)).hexdigest()[:16]

require(openapi_evidence.get("openapi_version") == committed_openapi.get("openapi"), "OpenAPI version mismatch")
require(openapi_evidence.get("title") == committed_openapi.get("info", {}).get("title"), "OpenAPI title mismatch")
require(openapi_evidence.get("api_version") == committed_openapi.get("info", {}).get("version"), "OpenAPI API version mismatch")
require(openapi_evidence.get("path_count") == len(paths), "OpenAPI path count mismatch")
require(openapi_evidence.get("schema_count") == len(schemas), "OpenAPI schema count mismatch")
require(openapi_evidence.get("sha256_prefix") == openapi_hash, "OpenAPI hash prefix mismatch")

public_demo_paths = openapi_evidence.get("public_demo_paths", [])
require(isinstance(public_demo_paths, list) and public_demo_paths, "missing public demo paths")
for path in public_demo_paths:
    require(path in paths, f"OpenAPI missing public demo path: {path}")

required_public_paths = {
    "/demo/public",
    "/demo/connector-certification",
    "/demo/provider-onboarding",
    "/demo/connector-fixture-replay",
    "/demo/business-intake-pipeline",
    "/demo/business-task-handoff",
    "/demo/business-notification-channels",
    "/demo/notification-delivery",
    "/demo/business-context-assistant",
    "/demo/business-action-execution",
    "/demo/business-approval-gateway",
    "/demo/integration-runtime",
    "/demo/integration-execution",
    "/demo/integration-repair",
    "/demo/observability-dashboard",
    "/demo/business-scenario-replay",
}
require(set(public_demo_paths) >= required_public_paths, "OpenAPI drift evidence missing required demo paths")

sdk_evidence = evidence.get("sdk", {}) if isinstance(evidence.get("sdk"), dict) else {}
require(sdk_manifest.get("source") == "docs/openapi.json", "SDK manifest source mismatch")
require(sdk_manifest.get("schema_version") == 1, "SDK manifest schema version mismatch")
require(sdk_manifest.get("data_profile") == "synthetic_demo_data", "SDK manifest data profile mismatch")
require(sdk_evidence.get("source") == sdk_manifest.get("source"), "SDK evidence source mismatch")
require(sdk_evidence.get("schema_version") == sdk_manifest.get("schema_version"), "SDK evidence schema mismatch")
require(sdk_evidence.get("data_profile") == sdk_manifest.get("data_profile"), "SDK evidence data profile mismatch")
require(sdk_evidence.get("sha256_prefix") == sdk_hash, "SDK manifest hash prefix mismatch")
require(sdk_evidence.get("generated_files") == sdk_manifest.get("generated_files"), "SDK generated files mismatch")

manifest_operation_paths = {
    value.get("path")
    for value in sdk_manifest.values()
    if isinstance(value, dict) and isinstance(value.get("path"), str)
}
if isinstance(sdk_manifest.get("path"), str):
    manifest_operation_paths.add(str(sdk_manifest["path"]))
for path in required_public_paths:
    require(path in manifest_operation_paths, f"SDK manifest missing operation path: {path}")

demo_data = read(demo_data_path)
for marker in [
    "DRIVEDESK_DEMO_DATA",
    "notificationDelivery",
    "businessScenarioReplay",
    "integrationExecution",
    "observabilityDashboard",
    "engineeringProof",
]:
    require(marker in demo_data, f"static demo payload missing marker: {marker}")

health_doc = read(public_demo_health_path)
for token in ["docs/openapi.json", "sdk/generated/public-demo/openapi-client-manifest.json"]:
    require(token in health_doc, f"public demo health missing OpenAPI/SDK token: {token}")

checks = evidence.get("checks", {}) if isinstance(evidence.get("checks"), dict) else {}
for check in [
    "committed_openapi_present",
    "generated_openapi_matches_committed",
    "public_demo_paths_present",
    "sdk_manifest_present",
    "sdk_manifest_source_matches",
    "sdk_manifest_operations_match",
    "static_demo_payload_markers_present",
    "public_demo_health_links_openapi",
    "ci_smoke_includes_check",
    "public_export_includes_check",
    "release_gate_includes_check",
]:
    require(checks.get(check) is True, f"OpenAPI drift evidence check failed: {check}")
require(checks.get("production_data_touched") is False, "OpenAPI drift touches production data")

redaction = evidence.get("redaction", {}) if isinstance(evidence.get("redaction"), dict) else {}
for key in [
    "addresses_included",
    "credentials_included",
    "hostnames_included",
    "paths_included",
    "production_data_included",
    "raw_logs_included",
    "request_bodies_included",
    "secrets_included",
]:
    require(redaction.get(key) is False, f"redaction flag must be false: {key}")

doc = read(doc_path)
for token in [
    "OpenAPI Drift Evidence",
    "docs/openapi.json",
    "app.openapi()",
    "sdk/generated/public-demo/openapi-client-manifest.json",
    "docs/public/evidence/openapi-drift.sanitized.json",
    "bash scripts/check_public_openapi_drift.sh",
    "bash scripts/ci_smoke_public.sh",
    "bash scripts/public_repo_release_gate.sh",
]:
    require(token in doc, f"OpenAPI drift doc missing {token}")

for path, name in [
    (docs_readme_path, "public docs README"),
    (evidence_index_path, "evidence index"),
    (project_status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_map_path, "technical capability map"),
]:
    text = read(path)
    require("OPENAPI_DRIFT.md" in text, f"{name} missing OpenAPI drift doc link")
    require("openapi-drift.sanitized.json" in text, f"{name} missing OpenAPI drift evidence")
    require("check_public_openapi_drift.sh" in text, f"{name} missing OpenAPI drift checker")

if evidence_index_json_path.is_file():
    index = json.loads(read(evidence_index_json_path))
    entries = index.get("entries", [])
    require(
        any(entry.get("capability_id") == "openapi-drift" for entry in entries if isinstance(entry, dict)),
        "evidence index JSON missing openapi-drift entry",
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
serialized = json.dumps(evidence, ensure_ascii=False, sort_keys=True) + doc
for pattern in private_patterns:
    require(not pattern.search(serialized), f"private marker leaked into OpenAPI drift evidence: {pattern.pattern}")

if is_public_export:
    public_smoke = read(public_smoke_path)
    require("check_public_openapi_drift.sh" in public_smoke, "public smoke missing OpenAPI drift checker")
else:
    export_script = read(export_script_path)
    private_smoke = read(private_smoke_path)
    release_gate = read(release_gate_path)
    for token in [
        'copy_path "scripts/check_public_openapi_drift.sh"',
        "OPENAPI_DRIFT.md",
        "openapi-drift.sanitized.json",
        "check_public_openapi_drift.sh",
        "docs/openapi.json",
        "openapi-client-manifest.json",
    ]:
        require(token in export_script, f"export script missing OpenAPI drift token: {token}")
    require("check_public_openapi_drift.sh" in private_smoke, "private smoke missing OpenAPI drift checker")
    require("check_public_openapi_drift.sh" in release_gate, "release gate missing OpenAPI drift checker")
    require("docs/public/OPENAPI_DRIFT.md" in release_gate, "release gate missing OpenAPI drift doc required file")
    require(
        "docs/public/evidence/openapi-drift.sanitized.json" in release_gate,
        "release gate missing OpenAPI drift evidence required file",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "public OpenAPI drift check ok: "
    f"paths={len(paths)} schemas={len(schemas)} sha256_prefix={openapi_hash}"
)
PY
