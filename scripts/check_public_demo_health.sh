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

export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" - <<'PY' "$ROOT"
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        errors.append(f"missing json file: {path.relative_to(root)}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
doc_path = root / "docs/public/PUBLIC_DEMO_HEALTH.md"
evidence_path = root / "docs/public/evidence/public-demo-health.sanitized.json"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
docs_readme_path = root / "docs/public/README.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
workflow_path = root / ".github/workflows/public-demo-health.yml"

for path in [
    doc_path,
    evidence_path,
    evidence_index_path,
    evidence_index_json_path,
    docs_readme_path,
    project_status_path,
    roadmap_path,
    capability_map_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

evidence = load_json(evidence_path)
require(evidence.get("schema_version") == 1, "public demo health schema version mismatch")
require(evidence.get("check") == "public_demo_health", "public demo health check mismatch")
require(evidence.get("status") == "validated", "public demo health status mismatch")
require(evidence.get("data_profile") == "synthetic_demo_data", "public demo health data profile mismatch")
require(evidence.get("health_model") == "pages_static_demo_ci_health", "public demo health model mismatch")
require(
    evidence.get("public_demo_url") == "https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/",
    "public demo URL mismatch",
)

workflow = evidence.get("workflow", {}) if isinstance(evidence.get("workflow"), dict) else {}
require(workflow.get("name") == "Public Demo Health", "workflow name mismatch")
require(workflow.get("path") == ".github/workflows/public-demo-health.yml", "workflow path mismatch")
require(set(workflow.get("trigger_modes", [])) == {"workflow_dispatch", "schedule"}, "workflow trigger modes mismatch")
require(workflow.get("cron_utc") == "17 */6 * * *", "workflow cron mismatch")
require(workflow.get("timeout_minutes") == 6, "workflow timeout mismatch")

checks = evidence.get("checks", {}) if isinstance(evidence.get("checks"), dict) else {}
for check in [
    "public_export_generates_workflow",
    "workflow_dispatch_present",
    "schedule_present",
    "pages_root_linked",
    "demo_shell_checked",
    "static_fallback_checked",
    "openapi_artifact_checked",
    "generated_sdk_checked",
    "notification_delivery_checked",
    "business_scenario_replay_checked",
    "engineering_proof_checked",
    "public_docs_linked",
]:
    require(checks.get(check) is True, f"public demo health evidence check failed: {check}")
require(checks.get("production_data_touched") is False, "public demo health touches production data")

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

for marker in [
    "DRIVEDESK_DEMO_DATA",
    "notificationDelivery",
    "businessScenarioReplay",
    "integrationExecution",
    "engineeringProof",
    "static.fallback",
]:
    require(marker in evidence.get("payload_markers", []), f"missing payload marker: {marker}")

doc = read(doc_path)
for token in [
    "Public Demo Health",
    "docs/public/evidence/public-demo-health.sanitized.json",
    ".github/workflows/public-demo-health.yml",
    "workflow_dispatch",
    "schedule",
    "apps/admin/public-demo/",
    "demo-data.js",
    "docs/openapi.json",
    "notificationDelivery",
    "businessScenarioReplay",
    "integrationExecution",
    "engineeringProof",
    "bash scripts/check_public_demo_health.sh",
]:
    require(token in doc, f"public demo health doc missing {token}")

for path, name in [
    (docs_readme_path, "public docs README"),
    (project_status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_map_path, "technical capability map"),
    (evidence_index_path, "evidence index"),
]:
    text = read(path)
    require("PUBLIC_DEMO_HEALTH.md" in text, f"{name} missing public demo health doc link")
    require("public-demo-health.sanitized.json" in text, f"{name} missing public demo health evidence")
    require("check_public_demo_health.sh" in text, f"{name} missing public demo health checker")

if evidence_index_json_path.is_file():
    index = json.loads(read(evidence_index_json_path))
    entries = index.get("entries", [])
    require(
        any(entry.get("capability_id") == "public-demo-health" for entry in entries if isinstance(entry, dict)),
        "evidence index JSON missing public-demo-health entry",
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
    require(not pattern.search(serialized), f"private marker leaked into public demo health: {pattern.pattern}")

if is_public_export:
    workflow_text = read(workflow_path)
    require(workflow_path.is_file(), "public export missing public demo health workflow")
    for token in [
        "name: Public Demo Health",
        "workflow_dispatch:",
        "schedule:",
        'cron: "17 */6 * * *"',
        "timeout-minutes: 6",
        "curl -fsSL --retry 3 --retry-delay 5",
        "DriveDesk Core Demo",
        "demo-data.js",
        "DRIVEDESK_DEMO_DATA",
        "notificationDelivery",
        "businessScenarioReplay",
        "integrationExecution",
        "openapi-client-manifest.json",
        "docs/openapi.json",
    ]:
        require(token in workflow_text, f"public demo health workflow missing {token}")
    require("check_public_demo_health.sh" in read(public_smoke_path), "public smoke missing public demo health checker")
else:
    export_script = read(export_script_path)
    for token in [
        'cat > "$EXPORT_DIR/.github/workflows/public-demo-health.yml"',
        "name: Public Demo Health",
        "workflow_dispatch:",
        "schedule:",
        'cron: "17 */6 * * *"',
        "timeout-minutes: 6",
        "notificationDelivery",
        "businessScenarioReplay",
        "integrationExecution",
        "openapi-client-manifest.json",
        "docs/openapi.json",
        "PUBLIC_DEMO_HEALTH.md",
        "public-demo-health.sanitized.json",
        'copy_path "scripts/check_public_demo_health.sh"',
    ]:
        require(token in export_script, f"export script missing public demo health token: {token}")
    require("check_public_demo_health.sh" in read(private_smoke_path), "private smoke missing public demo health checker")
    require("check_public_demo_health.sh" in read(release_gate_path), "release gate missing public demo health checker")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public demo health contract ok")
PY
