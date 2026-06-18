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
contract_path = root / "infra/observability/alert-routing.sanitized.json"
evidence_path = root / "docs/public/evidence/alert-routing.sanitized.json"
doc_path = root / "docs/public/ALERT_ROUTING_EVIDENCE.md"
adr_path = root / "docs/adr/0063-public-safe-alert-routing-evidence.md"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
roadmap_path = root / "docs/public/ROADMAP.md"
observability_doc_path = root / "docs/public/OBSERVABILITY_PROOF.md"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
root_readme_path = root / "README.md"
index_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"

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


contract = load_json(contract_path)
evidence = load_json(evidence_path)
require(contract == evidence, "alert routing contract and public evidence differ")

for payload_name, payload in [("contract", contract), ("evidence", evidence)]:
    require(payload.get("schema_version") == 1, f"{payload_name} schema_version mismatch")
    require(payload.get("check") == "public_alert_routing_evidence", f"{payload_name} check mismatch")
    require(
        payload.get("routing_model") == "alertmanager_style_route_tree",
        f"{payload_name} routing model mismatch",
    )
    require(payload.get("data_profile") == "synthetic_demo_data", f"{payload_name} data profile mismatch")

routes = contract.get("routes", []) if isinstance(contract.get("routes"), list) else []
receivers = contract.get("receivers", []) if isinstance(contract.get("receivers"), list) else []
bindings = contract.get("alert_bindings", []) if isinstance(contract.get("alert_bindings"), list) else []

route_names = {route.get("name") for route in routes if isinstance(route, dict)}
receiver_names = {receiver.get("name") for receiver in receivers if isinstance(receiver, dict)}
binding_alerts = {binding.get("alert") for binding in bindings if isinstance(binding, dict)}

for route_name in [
    "platform-critical-page",
    "platform-warning-ticket",
    "scheduled-validation-notice",
]:
    require(route_name in route_names, f"missing alert route: {route_name}")

for receiver_name in [
    "public-oncall-page",
    "public-chat-notice",
    "public-ticket-queue",
]:
    require(receiver_name in receiver_names, f"missing receiver: {receiver_name}")

for alert_name in [
    "DriveDeskApiTargetDown",
    "DriveDeskApiHighLatencyP95",
    "DriveDeskIntegrationDeadLetters",
    "DriveDeskAuthFailureSpike",
    "DriveDeskScheduledValidationMissed",
]:
    require(alert_name in binding_alerts, f"missing alert binding: {alert_name}")

for route in routes:
    if not isinstance(route, dict):
        continue
    require(route.get("receiver") in receiver_names, f"route receiver missing: {route}")
    require(route.get("runbook_required") is True, f"route runbook not required: {route.get('name')}")
    require(bool(route.get("failure_artifact")), f"route failure artifact missing: {route.get('name')}")
    require(int(route.get("repeat_interval_minutes", 0)) >= 30, f"route repeat interval too small: {route.get('name')}")
    require(bool(route.get("group_by")), f"route group_by missing: {route.get('name')}")

for receiver in receivers:
    if not isinstance(receiver, dict):
        continue
    require(receiver.get("external_secret_included") is False, f"receiver includes external secret: {receiver}")
    require(receiver.get("private_destination_included") is False, f"receiver includes private destination: {receiver}")
    require(receiver.get("payload_body_included") is False, f"receiver includes payload body: {receiver}")

for binding in bindings:
    if not isinstance(binding, dict):
        continue
    require(binding.get("route") in route_names, f"binding route missing: {binding}")
    require(binding.get("escalation_receiver") in receiver_names, f"binding escalation receiver missing: {binding}")
    require(str(binding.get("runbook", "")).startswith("docs/public/"), f"binding runbook is not public: {binding}")
    require((root / str(binding.get("runbook"))).is_file(), f"binding runbook target missing: {binding.get('runbook')}")
    require(bool(binding.get("dedupe_key")), f"binding dedupe key missing: {binding.get('alert')}")
    require(binding.get("severity") in {"critical", "warning"}, f"binding severity invalid: {binding}")
    require(binding.get("owner") in {"platform", "integrations", "security"}, f"binding owner invalid: {binding}")

runbook_contract = contract.get("runbook_contract", {}) if isinstance(contract.get("runbook_contract"), dict) else {}
for required_field in [
    "alert",
    "severity",
    "service",
    "owner",
    "first_action",
    "evidence_artifact",
    "rollback_or_mitigation",
]:
    require(required_field in runbook_contract.get("required_fields", []), f"runbook field missing: {required_field}")
require(runbook_contract.get("raw_logs_required") is False, "runbook requires raw logs")
require(runbook_contract.get("request_body_required") is False, "runbook requires request bodies")
require(runbook_contract.get("private_runtime_access_required") is False, "runbook requires private runtime access")
require(runbook_contract.get("sanitized_evidence_required") is True, "runbook does not require sanitized evidence")

silence_contract = contract.get("silence_contract", {}) if isinstance(contract.get("silence_contract"), dict) else {}
require(silence_contract.get("planned_maintenance_supported") is True, "planned maintenance silence missing")
require(silence_contract.get("max_duration_minutes") == 120, "silence max duration mismatch")
require(silence_contract.get("audit_event") == "alert.silence.created", "silence audit event mismatch")
for matcher in ["alertname", "service", "stage"]:
    require(matcher in silence_contract.get("required_matchers", []), f"silence matcher missing: {matcher}")

checks = contract.get("checks", {}) if isinstance(contract.get("checks"), dict) else {}
for check in [
    "routes_present",
    "receivers_present",
    "critical_route_present",
    "warning_route_present",
    "scheduled_validation_route_present",
    "alerts_bound_to_routes",
    "runbooks_required",
    "dedupe_keys_recorded",
    "escalation_recorded",
    "silence_contract_recorded",
    "failure_artifacts_recorded",
    "external_notification_secrets_absent",
    "private_destinations_absent",
    "payload_bodies_absent",
    "public_docs_linked",
    "private_markers_absent",
]:
    require(checks.get(check) is True, f"alert routing check failed: {check}")
require(checks.get("production_data_touched") is False, "alert routing touches production data")

redaction = contract.get("redaction", {}) if isinstance(contract.get("redaction"), dict) else {}
for key in [
    "paths_included",
    "hostnames_included",
    "addresses_included",
    "credentials_included",
    "raw_logs_included",
    "request_bodies_included",
    "production_data_included",
]:
    require(redaction.get(key) is False, f"redaction flag not false: {key}")

doc = read(doc_path)
for token in [
    "Alert Routing Evidence",
    "docs/public/evidence/alert-routing.sanitized.json",
    "infra/observability/alert-routing.sanitized.json",
    "bash scripts/check_public_alert_routing.sh",
    "platform-critical-page",
    "public-oncall-page",
    "DriveDeskScheduledValidationMissed",
    "INCIDENT_RESPONSE_DEMO.md",
    "alert.silence.created",
    "public-safe routing proof",
]:
    require(token in doc, f"alert routing doc missing {token}")

demo_html = read(demo_html_path)
for token in [
    'data-view="operations"',
    "Operations Control",
    "alertRoutingSummaryRows",
    "alertRouteRows",
    "alertBindingRows",
    "alertRunbookRows",
]:
    require(token in demo_html, f"public demo HTML missing alert routing token: {token}")

demo_app = read(demo_app_path)
for token in [
    "fillAlertRouting",
    "alertRouting",
    "routing.routes",
    "routing.bindings",
    "routing.runbookActions",
]:
    require(token in demo_app, f"public demo app missing alert routing token: {token}")

demo_data = read(demo_data_path)
for token in [
    '"alertRouting"',
    "platform-critical-page",
    "platform-warning-ticket",
    "scheduled-validation-notice",
    "DriveDeskScheduledValidationMissed",
    "alert.silence.created",
]:
    require(token in demo_data, f"public demo data missing alert routing token: {token}")

adr = read(adr_path)
for token in [
    "ADR-0063",
    "Public-Safe Alert Routing Evidence",
    "scripts/check_public_alert_routing.sh",
    "alert-routing.sanitized.json",
]:
    require(token in adr, f"alert routing ADR missing {token}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (review_guide_path, "review guide"),
    (project_status_path, "project status"),
    (capability_map_path, "technical capability map"),
    (roadmap_path, "roadmap"),
    (observability_doc_path, "observability proof"),
]:
    require("ALERT_ROUTING_EVIDENCE.md" in read(doc_path), f"{label} missing ALERT_ROUTING_EVIDENCE.md")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for path in [
        "README.md",
        "index.html",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_export_secrets.sh",
    ]:
        require((root / path).is_file(), f"public export target missing: {path}")
    require("ALERT_ROUTING_EVIDENCE.md" in read(root_readme_path), "public README missing alert routing evidence")
    require("ALERT_ROUTING_EVIDENCE.md" in read(index_path), "public Pages root missing alert routing evidence")
    require(
        "check_public_alert_routing.sh" in read(public_smoke_path),
        "public smoke missing alert routing check",
    )
else:
    export_script = read(export_script_path)
    require('copy_path "infra/observability"' in export_script, "export script missing observability evidence dir")
    require("ALERT_ROUTING_EVIDENCE.md" in export_script, "export script missing alert routing evidence")
    require(
        'copy_path "scripts/check_public_alert_routing.sh"' in export_script,
        "export script missing alert routing check copy",
    )
    require(
        "0063-public-safe-alert-routing-evidence.md" in export_script,
        "export script missing alert routing ADR",
    )
    require(
        "check_public_alert_routing.sh" in read(private_smoke_path),
        "private smoke missing alert routing check",
    )
    require(
        "check_public_alert_routing.sh" in read(release_gate_path),
        "release gate missing alert routing check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_alert_routing.sh" in read(public_smoke_path),
        "public smoke missing alert routing check",
    )

private_patterns = [
    r"auto\s*" + r"school\s*54",
    "auto" + "school54",
    "land" + "vps",
    "duck" + "dns",
    "215" + "689",
    "185" + r"\.80\.",
    "152" + r"\.53\.",
    "2a0a:",
    "/" + "opt/",
    "xr" + "ay",
]
scan_text = "\n".join(
    [
        json.dumps(contract, sort_keys=True),
        doc,
        adr,
    ]
).lower()
for pattern in private_patterns:
    require(re.search(pattern, scan_text) is None, f"runtime marker leaked into alert routing evidence: {pattern}")

if errors:
    for error in errors:
        print(f"alert_routing_error={error}", file=sys.stderr)
    raise SystemExit("public alert routing check failed")

print(
    "public alert routing check ok: "
    f"routes={len(routes)} receivers={len(receivers)} alerts={len(bindings)}"
)
PY
