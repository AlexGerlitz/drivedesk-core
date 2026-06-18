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
contract_path = root / "infra/observability/observability-proof.sanitized.json"
evidence_path = root / "docs/public/evidence/observability-proof.sanitized.json"
doc_path = root / "docs/public/OBSERVABILITY_PROOF.md"
adr_path = root / "docs/adr/0062-public-safe-observability-proof.md"
docs_readme_path = root / "docs/public/README.md"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
project_status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
roadmap_path = root / "docs/public/ROADMAP.md"
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
require(contract == evidence, "observability proof contract and public evidence differ")

for payload_name, payload in [("contract", contract), ("evidence", evidence)]:
    require(payload.get("schema_version") == 1, f"{payload_name} schema_version mismatch")
    require(payload.get("check") == "public_observability_proof", f"{payload_name} check mismatch")
    require(
        payload.get("observability_model") == "metrics_logs_alerts_dashboards",
        f"{payload_name} observability model mismatch",
    )
    require(payload.get("data_profile") == "synthetic_demo_data", f"{payload_name} data profile mismatch")

signals = contract.get("signals", {}) if isinstance(contract.get("signals"), dict) else {}
metrics = signals.get("metrics", []) if isinstance(signals.get("metrics"), list) else []
logs = signals.get("logs", []) if isinstance(signals.get("logs"), list) else []
alerts = signals.get("alerts", []) if isinstance(signals.get("alerts"), list) else []
dashboards = signals.get("dashboards", []) if isinstance(signals.get("dashboards"), list) else []

metric_names = {metric.get("name") for metric in metrics if isinstance(metric, dict)}
for metric in [
    "drivedesk_http_requests_total",
    "drivedesk_http_request_duration_seconds_bucket",
    "drivedesk_outbox_events",
    "drivedesk_integration_jobs",
    "drivedesk_auth_attempts_total",
]:
    require(metric in metric_names, f"missing metric signal: {metric}")

for metric in metrics:
    if not isinstance(metric, dict):
        continue
    labels = set(metric.get("safe_labels", []))
    forbidden_labels = {"email", "user_id", "tenant_id", "token", "phone", "name", "payload"}
    require(labels.isdisjoint(forbidden_labels), f"unsafe metric labels on {metric.get('name')}")

log_events = {log.get("event_type") for log in logs if isinstance(log, dict)}
for event_type in [
    "api.request.completed",
    "adapter.completed",
    "outbox_event.retry_requested",
]:
    require(event_type in log_events, f"missing log event: {event_type}")
for log in logs:
    if isinstance(log, dict):
        require(log.get("raw_payload_included") is False, f"raw payload included in log {log.get('event_type')}")

alert_names = {alert.get("name") for alert in alerts if isinstance(alert, dict)}
for alert in [
    "DriveDeskApiTargetDown",
    "DriveDeskApiHighLatencyP95",
    "DriveDeskIntegrationDeadLetters",
    "DriveDeskAuthFailureSpike",
    "DriveDeskNoRecentLogs",
]:
    require(alert in alert_names, f"missing alert signal: {alert}")
for alert in alerts:
    if not isinstance(alert, dict):
        continue
    require(bool(alert.get("runbook")), f"alert runbook missing: {alert.get('name')}")
    require(str(alert.get("runbook", "")).startswith("docs/public/"), f"alert runbook is not public doc: {alert}")
    require((root / str(alert.get("runbook"))).is_file(), f"alert runbook target missing: {alert.get('runbook')}")

dashboard_titles = {dashboard.get("title") for dashboard in dashboards if isinstance(dashboard, dict)}
for title in [
    "API availability and latency",
    "Outbox and integration health",
    "Auth and workflow health",
    "Structured logs by service",
]:
    require(title in dashboard_titles, f"missing dashboard: {title}")

checks = contract.get("checks", {}) if isinstance(contract.get("checks"), dict) else {}
for check in [
    "metrics_present",
    "metrics_use_safe_labels",
    "structured_logs_present",
    "raw_log_payloads_absent",
    "alerts_have_runbooks",
    "dashboard_panels_reference_metrics_and_logs",
    "loki_signal_present",
    "prometheus_rule_signal_present",
    "public_docs_linked",
    "private_markers_absent",
]:
    require(checks.get(check) is True, f"observability check failed: {check}")
require(checks.get("production_data_touched") is False, "observability proof touches production data")

redaction = contract.get("redaction", {}) if isinstance(contract.get("redaction"), dict) else {}
for key in [
    "paths_included",
    "hostnames_included",
    "addresses_included",
    "credentials_included",
    "raw_logs_included",
    "production_data_included",
]:
    require(redaction.get(key) is False, f"redaction flag not false: {key}")

doc = read(doc_path)
for token in [
    "Observability Proof",
    "metrics, structured logs, alert rules",
    "docs/public/evidence/observability-proof.sanitized.json",
    "infra/observability/observability-proof.sanitized.json",
    "bash scripts/check_public_observability_proof.sh",
    "drivedesk_http_requests_total",
    "api.request.completed",
    "DriveDeskNoRecentLogs",
    "Dashboard Contract",
    "Alert Contract",
    "This is a public-safe proof of the observability loop",
]:
    require(token in doc, f"observability proof doc missing {token}")

adr = read(adr_path)
for token in [
    "ADR-0062",
    "Public-Safe Observability Proof",
    "metrics, logs, alerts",
    "scripts/check_public_observability_proof.sh",
]:
    require(token in adr, f"observability proof ADR missing {token}")

for doc_path, label in [
    (docs_readme_path, "docs/public README"),
    (review_guide_path, "review guide"),
    (project_status_path, "project status"),
    (capability_map_path, "technical capability map"),
    (roadmap_path, "roadmap"),
]:
    require("OBSERVABILITY_PROOF.md" in read(doc_path), f"{label} missing OBSERVABILITY_PROOF.md")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    for path in [
        "README.md",
        "index.html",
        "scripts/ci_smoke_public.sh",
        "scripts/check_public_export_secrets.sh",
    ]:
        require((root / path).is_file(), f"public export target missing: {path}")
    require("OBSERVABILITY_PROOF.md" in read(root_readme_path), "public README missing observability proof")
    require("OBSERVABILITY_PROOF.md" in read(index_path), "public Pages root missing observability proof")
    require(
        "check_public_observability_proof.sh" in read(public_smoke_path),
        "public smoke missing observability proof check",
    )
else:
    export_script = read(export_script_path)
    require('copy_path "infra/observability"' in export_script, "export script missing observability evidence dir")
    require("OBSERVABILITY_PROOF.md" in export_script, "export script missing observability proof")
    require(
        'copy_path "scripts/check_public_observability_proof.sh"' in export_script,
        "export script missing observability proof check copy",
    )
    require(
        "0062-public-safe-observability-proof.md" in export_script,
        "export script missing observability proof ADR",
    )
    require(
        "check_public_observability_proof.sh" in read(private_smoke_path),
        "private smoke missing observability proof check",
    )
    require(
        "check_public_observability_proof.sh" in read(release_gate_path),
        "release gate missing observability proof check",
    )

if public_smoke_path.is_file():
    require(
        "check_public_observability_proof.sh" in read(public_smoke_path),
        "public smoke missing observability proof check",
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
    require(re.search(pattern, scan_text) is None, f"runtime marker leaked into observability proof: {pattern}")

if errors:
    for error in errors:
        print(f"observability_proof_error={error}", file=sys.stderr)
    raise SystemExit("public observability proof check failed")

print(
    "public observability proof check ok: "
    f"metrics={len(metrics)} logs={len(logs)} alerts={len(alerts)} dashboards={len(dashboards)}"
)
PY
