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

import json
import re
import sys
from pathlib import Path

from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.main import build_app

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


def parse_static_demo_data(path: Path) -> dict[str, object]:
    text = read(path)
    match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", text, re.S)
    require(match is not None, "static demo data assignment not found")
    return json.loads(match.group(1)) if match else {}


source_evidence_path = root / "infra/notifications/notification-delivery.sanitized.json"
public_evidence_path = root / "docs/public/evidence/notification-delivery.sanitized.json"
doc_path = root / "docs/public/NOTIFICATION_DELIVERY.md"
adr_path = root / "docs/adr/0077-public-safe-notification-delivery.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
demo_py_path = root / "apps/api/drivedesk_api/demo.py"
main_path = root / "apps/api/drivedesk_api/main.py"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
openapi_path = root / "docs/openapi.json"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
docs_readme_path = root / "docs/public/README.md"
evidence_index_path = root / "docs/public/EVIDENCE_INDEX.md"
evidence_index_json_path = root / "docs/public/evidence/public-evidence-index.sanitized.json"
review_guide_path = root / "docs/public/ENGINEERING_REVIEW_GUIDE.md"
export_script_path = root / "scripts/export_public_repo.sh"
ci_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [
    source_evidence_path,
    public_evidence_path,
    doc_path,
    adr_path,
    demo_data_path,
    demo_html_path,
    demo_app_path,
    demo_py_path,
    main_path,
    schemas_path,
    openapi_path,
    api_demo_doc_path,
    capability_map_path,
    status_path,
    roadmap_path,
    docs_readme_path,
    evidence_index_path,
    review_guide_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

source_evidence = load_json(source_evidence_path)
public_evidence = load_json(public_evidence_path)
require(source_evidence == public_evidence, "notification delivery source and public evidence differ")
require(source_evidence.get("schema_version") == 1, "notification delivery schema version mismatch")
require(source_evidence.get("check") == "public_notification_delivery", "notification delivery check mismatch")
require(source_evidence.get("delivery_model") == "outbox_worker_provider_gate", "delivery model mismatch")
require(source_evidence.get("data_profile") == "synthetic_demo_data", "data profile mismatch")
require(source_evidence.get("status") == "validated", "notification delivery evidence status mismatch")
require(
    set(source_evidence.get("channels", [])) == {"in_app", "telegram", "email", "sms", "webhook"},
    "notification delivery evidence channel set mismatch",
)
require(
    set(source_evidence.get("recovery_paths", []))
    == {"short_retry", "dead_letter_after_exhaustion", "operator_review"},
    "notification delivery recovery paths mismatch",
)

checks = source_evidence.get("checks", {}) if isinstance(source_evidence.get("checks"), dict) else {}
for check in [
    "adapter_profiles_present",
    "delivery_stages_present",
    "outbox_events_present",
    "retry_policy_present",
    "dead_letter_plan_present",
    "observability_present",
    "public_demo_payload_present",
    "openapi_path_present",
    "public_docs_linked",
    "private_markers_absent",
]:
    require(checks.get(check) is True, f"notification delivery evidence check failed: {check}")
require(checks.get("production_data_touched") is False, "notification delivery touches production data")

redaction = source_evidence.get("redaction", {}) if isinstance(source_evidence.get("redaction"), dict) else {}
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

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
delivery = api_payload.get("notificationDelivery", {})
static_delivery = static_payload.get("notificationDelivery", {})

require(delivery == static_delivery, "API and static notificationDelivery differ")
require(delivery.get("status") == "validated", "notificationDelivery status mismatch")
require(delivery.get("command") == "GET /demo/notification-delivery", "notificationDelivery command mismatch")
require(delivery.get("deliveryLevel") == "delivery_runtime_ready", "notificationDelivery level mismatch")
require(delivery.get("deliveryRuntime") == "outbox_worker_provider_gate", "delivery runtime mismatch")
require(delivery.get("subject") == "deal:DEAL-2026-001", "notification delivery subject mismatch")
require(
    {item.get("label") for item in delivery.get("summary", [])}
    >= {"Channels", "Outbox events", "Provider calls", "Recovery paths"},
    "notificationDelivery summary missing labels",
)

profiles = delivery.get("adapterProfiles", [])
profile_by_channel = {item.get("channel"): item for item in profiles if isinstance(item, dict)}
require(set(profile_by_channel) == {"in_app", "telegram", "email", "sms", "webhook"}, "adapter profile set mismatch")
for channel, profile in profile_by_channel.items():
    require(profile.get("providerCallEnabled") is False, f"{channel} provider call enabled")
    require(profile.get("externalDelivery") is False, f"{channel} external delivery enabled")
    require(
        profile.get("safePayloadProfile") == "role_subject_action_reference",
        f"{channel} safe payload profile mismatch",
    )
    require(str(profile.get("adapterKey", "")).startswith("notification."), f"{channel} adapter key mismatch")

stages = delivery.get("deliveryStages", [])
require(
    {item.get("stage") for item in stages}
    >= {
        "draft_prepared",
        "policy_checked",
        "outbox_enqueued",
        "worker_dispatched",
        "provider_gate_blocked",
        "retry_or_dead_letter",
    },
    "delivery stages mismatch",
)

outbox_events = delivery.get("outboxEvents", [])
require(len(outbox_events) == 5, "outbox event count mismatch")
require({item.get("channel") for item in outbox_events} == set(profile_by_channel), "outbox event channel mismatch")
for event in outbox_events:
    channel = event.get("channel")
    require(event.get("eventType") == "notification.delivery.requested", f"{channel} event type mismatch")
    require(str(event.get("idempotencyKey", "")).startswith("notification:deal:"), f"{channel} idempotency mismatch")
    require(event.get("providerCallEnabled") is False, f"{channel} outbox provider call enabled")
    require(event.get("externalDelivery") is False, f"{channel} outbox external delivery enabled")
    require(event.get("containsPii") is False, f"{channel} outbox contains PII")
    require(event.get("rawPayloadIncluded") is False, f"{channel} outbox raw payload included")

require(
    {item.get("name") for item in delivery.get("retryPolicy", [])}
    == {"short_retry", "dead_letter_after_exhaustion", "operator_review"},
    "retry policy mismatch",
)
require(
    {item.get("route") for item in delivery.get("deadLetterPlan", [])}
    == {"notifications.dead_letter", "integration.incident"},
    "dead-letter route mismatch",
)
signals = delivery.get("observability", [])
require(
    {item.get("name") for item in signals}
    >= {
        "drivedesk_notification_delivery_attempts_total",
        "drivedesk_notification_delivery_dead_letters_total",
        "notification.delivery.status_changed",
        "DriveDeskNotificationDeadLetters",
    },
    "observability signals mismatch",
)
for signal in signals:
    labels = set(signal.get("safeLabels", [])) if isinstance(signal, dict) else set()
    require(labels.isdisjoint({"email", "phone", "name", "token", "payload", "request_body"}), "unsafe observability labels")
    require(signal.get("containsPii") is False, "observability contains PII")
    require(signal.get("rawPayloadIncluded") is False, "observability includes raw payload")

for boundary in delivery.get("dataBoundaries", []):
    require(boundary.get("providerCallEnabled") is False, f"provider call enabled in boundary {boundary.get('name')}")
    require(boundary.get("rawPayloadIncluded") is not True, f"raw payload included in boundary {boundary.get('name')}")
    require(boundary.get("browserTokenStorage") is not True, f"browser token storage in boundary {boundary.get('name')}")

require(delivery.get("api", {}).get("standalone") == "GET /demo/notification-delivery", "standalone API mismatch")
require(
    {item.get("path") for item in delivery.get("docs", [])}
    >= {
        "docs/public/NOTIFICATION_DELIVERY.md",
        "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md",
        "docs/public/OUTBOX_RECOVERY.md",
    },
    "notificationDelivery docs mismatch",
)

serialized = json.dumps(delivery, ensure_ascii=False, sort_keys=True).lower()
for blocked in [
    "password",
    "authorization",
    "access_token",
    "bot_token",
    "bearer ",
    "+70000000000",
    "raw_payload",
    "request_body_value",
]:
    require(blocked not in serialized, f"notificationDelivery leaked blocked token: {blocked}")

openapi = load_json(openapi_path)
paths = openapi.get("paths", {}) if isinstance(openapi.get("paths"), dict) else {}
require("/demo/notification-delivery" in paths, "OpenAPI missing notification delivery demo endpoint")
require(
    paths.get("/demo/notification-delivery", {}).get("get", {}).get("operationId")
    == "notification_delivery_demo_demo_notification_delivery_get",
    "notification delivery operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require("NotificationDeliveryDemoRead" in components, "OpenAPI missing NotificationDeliveryDemoRead schema")
require(
    "notificationDelivery" in components.get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing notificationDelivery",
)
runtime_openapi = build_app().openapi()
require(
    "/demo/notification-delivery" in runtime_openapi.get("paths", {}),
    "runtime OpenAPI missing notification delivery demo",
)

html = read(demo_html_path)
for token in [
    "Notification Delivery",
    "notificationDeliverySummaryRows",
    "notificationDeliveryAdapterRows",
    "notificationDeliveryStageRows",
    "notificationDeliveryOutboxRows",
    "notificationDeliveryRecoveryRows",
    "notificationDeliveryBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "notificationDelivery",
    "fillNotificationDelivery",
    "notificationDeliverySummaryRows",
    "notificationDeliveryAdapterRows",
    "notificationDeliveryStageRows",
    "notificationDeliveryOutboxRows",
    "notificationDeliveryRecoveryRows",
    "notificationDeliveryBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

for path, name in [
    (doc_path, "notification delivery doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (roadmap_path, "roadmap"),
    (docs_readme_path, "public docs README"),
    (evidence_index_path, "evidence index"),
    (review_guide_path, "engineering review guide"),
]:
    text = read(path)
    require("NOTIFICATION_DELIVERY.md" in text, f"{name} missing notification delivery doc link")
    require("notificationDelivery" in text, f"{name} missing notificationDelivery token")
    require("GET /demo/notification-delivery" in text, f"{name} missing standalone endpoint")

adr = read(adr_path)
for token in [
    "ADR-0077",
    "Public-Safe Notification Delivery Runtime",
    "GET /demo/notification-delivery",
    "scripts/check_public_notification_delivery.sh",
]:
    require(token in adr, f"notification delivery ADR missing {token}")

demo_py = read(demo_py_path)
for token in [
    "_public_notification_delivery",
    "notificationDelivery",
    "notification_delivery.provider_gate_blocked",
    "drivedesk_notification_delivery_attempts_total",
]:
    require(token in demo_py, f"demo payload missing {token}")

main = read(main_path)
for token in [
    "NotificationDeliveryDemoRead",
    "/demo/notification-delivery",
    "notificationDelivery",
]:
    require(token in main, f"API main missing {token}")

schemas = read(schemas_path)
for token in [
    "class NotificationDeliveryDemoRead",
    "notificationDelivery",
    "deliveryStages",
    "outboxEvents",
]:
    require(token in schemas, f"schema missing {token}")

if sdk_manifest_path.is_file():
    manifest = json.loads(read(sdk_manifest_path))
    delivery_manifest = manifest.get("notification_delivery", {})
    require(delivery_manifest.get("path") == "/demo/notification-delivery", "SDK manifest delivery path mismatch")
    require(
        delivery_manifest.get("operation_id") == "notification_delivery_demo_demo_notification_delivery_get",
        "SDK manifest delivery operation id mismatch",
    )
    require("notificationDelivery" in manifest.get("required_fields", []), "SDK required fields missing notificationDelivery")

if is_public_export:
    require(
        "check_public_notification_delivery.sh" in read(public_smoke_path),
        "public smoke missing notification delivery check",
    )
else:
    require(
        'copy_path "docs/public/NOTIFICATION_DELIVERY.md"' in read(export_script_path),
        "export script missing notification delivery doc",
    )
    require(
        'copy_path "docs/adr/0077-public-safe-notification-delivery.md"' in read(export_script_path),
        "export script missing notification delivery ADR",
    )
    require(
        'copy_path "infra/notifications/notification-delivery.sanitized.json"' in read(export_script_path),
        "export script missing notification delivery source evidence",
    )
    require(
        'copy_path "scripts/check_public_notification_delivery.sh"' in read(export_script_path),
        "export script missing notification delivery checker",
    )
    require(
        "check_public_notification_delivery.sh" in read(ci_smoke_path),
        "private smoke missing notification delivery checker",
    )
    require(
        "check_public_notification_delivery.sh" in read(release_gate_path),
        "release gate missing notification delivery checker",
    )

if evidence_index_json_path.is_file():
    evidence_index = json.loads(read(evidence_index_json_path))
    entries = evidence_index.get("entries", [])
    require(
        any(entry.get("capability_id") == "notification-delivery" for entry in entries if isinstance(entry, dict)),
        "evidence index JSON missing notification-delivery entry",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public notification delivery contract ok")
PY
