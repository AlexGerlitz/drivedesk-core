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


def parse_static_demo_data(path: Path) -> dict[str, object]:
    text = read(path)
    match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", text, re.S)
    require(match is not None, "static demo data assignment not found")
    return json.loads(match.group(1)) if match else {}


doc_path = root / "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md"
api_demo_doc_path = root / "docs/public/API_BACKED_DEMO.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
docs_readme_path = root / "docs/public/README.md"
platform_tour_path = root / "docs/public/PLATFORM_TOUR.md"
system_review_path = root / "docs/public/SYSTEM_REVIEW_PATH.md"
roadmap_path = root / "docs/public/ROADMAP.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_html_path = root / "apps/admin/public-demo/index.html"
demo_app_path = root / "apps/admin/public-demo/app.js"
openapi_path = root / "docs/openapi.json"
schemas_path = root / "apps/api/drivedesk_api/schemas.py"
main_path = root / "apps/api/drivedesk_api/main.py"
services_path = root / "apps/api/drivedesk_api/services.py"
export_script_path = root / "scripts/export_public_repo.sh"
ci_smoke_path = root / "scripts/ci_smoke.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
sdk_generator_path = root / "scripts/generate_public_demo_sdk.py"
sdk_manifest_path = root / "sdk/generated/public-demo/openapi-client-manifest.json"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

for path in [
    doc_path,
    api_demo_doc_path,
    capability_map_path,
    status_path,
    docs_readme_path,
    platform_tour_path,
    system_review_path,
    roadmap_path,
    demo_data_path,
    demo_html_path,
    demo_app_path,
    openapi_path,
    schemas_path,
    main_path,
    services_path,
    sdk_generator_path,
]:
    require(path.is_file(), f"missing file: {path.relative_to(root)}")

api_payload = build_public_demo_payload()
static_payload = parse_static_demo_data(demo_data_path)
matrix = api_payload.get("businessNotificationChannels", {})
static_matrix = static_payload.get("businessNotificationChannels", {})

require(matrix == static_matrix, "API and static businessNotificationChannels differ")
require(matrix.get("status") == "previewed", "businessNotificationChannels status mismatch")
require(
    matrix.get("command") == "POST /tenants/{tenant_id}/business-notification-channels/preview",
    "businessNotificationChannels command mismatch",
)
require(
    {item.get("label") for item in matrix.get("summary", [])}
    >= {"Channels", "Internal ready", "Draft-only external", "External deliveries"},
    "businessNotificationChannels summary missing required labels",
)
require(matrix.get("role") == "accountant", "businessNotificationChannels role mismatch")
require(matrix.get("subject") == "deal:DEAL-2026-001", "businessNotificationChannels subject mismatch")

channels = matrix.get("channels", [])
channel_by_key = {item.get("channel"): item for item in channels if isinstance(item, dict)}
require(set(channel_by_key) == {"in_app", "telegram", "email", "sms", "webhook"}, "channel set mismatch")

in_app = channel_by_key.get("in_app", {})
require(in_app.get("status") == "ready", "in_app status mismatch")
require(in_app.get("configured") is True, "in_app must be configured")
require(in_app.get("requiresSecret") is False, "in_app must not require secret")
require(in_app.get("requiresPrivateConnector") is False, "in_app must not require private connector")
require(in_app.get("externalDelivery") is False, "in_app must not deliver externally")
require(in_app.get("containsPii") is False, "in_app contains PII")
require(in_app.get("rawPayloadIncluded") is False, "in_app includes raw payload")

external_statuses = {
    "telegram": "requires_private_secret",
    "email": "requires_private_secret",
    "sms": "requires_private_provider",
    "webhook": "requires_private_endpoint",
}
for channel, expected_status in external_statuses.items():
    item = channel_by_key.get(channel, {})
    require(item.get("status") == expected_status, f"{channel} status mismatch")
    require(item.get("configured") is False, f"{channel} must not be configured in public demo")
    require(item.get("requiresSecret") is True, f"{channel} must require secret")
    require(item.get("requiresPrivateConnector") is True, f"{channel} must require private connector")
    require(item.get("externalDelivery") is False, f"{channel} must not deliver externally")
    require(item.get("externalProviderMutation") is False, f"{channel} mutates provider")
    require(item.get("containsPii") is False, f"{channel} contains PII")
    require(item.get("rawPayloadIncluded") is False, f"{channel} includes raw payload")
    require(
        item.get("safePayloadProfile") == "role_subject_action_reference",
        f"{channel} safe payload profile mismatch",
    )
    require(
        item.get("evidence") == "business_notification_channel_matrix.previewed",
        f"{channel} evidence mismatch",
    )

require(
    {item.get("rule") for item in matrix.get("routingRules", [])}
    == {"prefer_internal_in_app", "external_channels_require_private_connector", "safe_payload_only"},
    "routing rules mismatch",
)

drafts = matrix.get("deliveryDrafts", [])
require(len(drafts) == 5, "delivery draft count mismatch")
require({item.get("channel") for item in drafts} == set(channel_by_key), "delivery draft channel set mismatch")
for draft in drafts:
    channel = draft.get("channel")
    expected_status = "ready" if channel == "in_app" else "draft_only"
    require(draft.get("status") == expected_status, f"{channel} draft status mismatch")
    require(
        draft.get("wouldEnqueueEvent") == "notification.delivery.requested",
        f"{channel} draft outbox event mismatch",
    )
    require(draft.get("externalDelivery") is False, f"{channel} draft sends externally")
    require(draft.get("containsPii") is False, f"{channel} draft contains PII")
    require(draft.get("rawPayloadIncluded") is False, f"{channel} draft includes raw payload")
    require(
        draft.get("safePayloadProfile") == "role_subject_action_reference",
        f"{channel} draft safe payload profile mismatch",
    )
    require(
        draft.get("evidence") == "business_notification_channel_matrix.previewed",
        f"{channel} draft evidence mismatch",
    )

require(
    {item.get("gate") for item in matrix.get("approvalGates", [])}
    == {"notification_content_review", "private_channel_secret_setup", "external_delivery_gate"},
    "approval gates mismatch",
)
require(
    {item.get("name") for item in matrix.get("dataBoundaries", [])}
    == {"preview_only_no_delivery", "server_secret_store_boundary", "safe_notification_payload"},
    "data boundaries mismatch",
)
require(
    {item.get("path") for item in matrix.get("docs", [])}
    >= {
        "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md",
        "docs/public/BUSINESS_TASK_HANDOFF.md",
        "docs/public/API_BACKED_DEMO.md",
    },
    "businessNotificationChannels docs mismatch",
)

serialized = json.dumps(matrix, ensure_ascii=False, sort_keys=True).lower()
for blocked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization"]:
    require(blocked not in serialized, f"businessNotificationChannels leaked blocked token: {blocked}")

openapi = json.loads(read(openapi_path) or "{}")
paths = openapi.get("paths", {})
require("/demo/business-notification-channels" in paths, "OpenAPI missing notification channels demo endpoint")
require(
    "/tenants/{tenant_id}/business-notification-channels/preview" in paths,
    "OpenAPI missing notification channels preview endpoint",
)
require(
    paths.get("/demo/business-notification-channels", {}).get("get", {}).get("operationId")
    == "business_notification_channels_demo_demo_business_notification_channels_get",
    "notification channels demo operation id mismatch",
)
components = openapi.get("components", {}).get("schemas", {})
require(
    "BusinessNotificationChannelMatrixDemoRead" in components,
    "OpenAPI missing BusinessNotificationChannelMatrixDemoRead schema",
)
require(
    "BusinessNotificationChannelMatrixPreviewRead" in components,
    "OpenAPI missing BusinessNotificationChannelMatrixPreviewRead schema",
)
require(
    "businessNotificationChannels"
    in components.get("PublicDemoRead", {}).get("required", []),
    "PublicDemoRead schema missing businessNotificationChannels",
)

app_openapi = build_app().openapi()
require(
    "/demo/business-notification-channels" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing notification channels demo",
)
require(
    "/tenants/{tenant_id}/business-notification-channels/preview" in app_openapi.get("paths", {}),
    "runtime OpenAPI missing notification channels preview",
)

html = read(demo_html_path)
for token in [
    "Notification Channels",
    "businessNotificationSummaryRows",
    "businessNotificationChannelRows",
    "businessNotificationDraftRows",
    "businessNotificationBoundaryRows",
]:
    require(token in html, f"public demo HTML missing {token}")

app_js = read(demo_app_path)
for token in [
    "businessNotificationChannels",
    "fillBusinessNotificationChannels",
    "businessNotificationSummaryRows",
    "businessNotificationChannelRows",
    "businessNotificationDraftRows",
    "businessNotificationBoundaryRows",
]:
    require(token in app_js, f"public demo app missing {token}")

for path, name in [
    (doc_path, "business notification channels doc"),
    (api_demo_doc_path, "API-backed demo doc"),
    (capability_map_path, "technical capability map"),
    (status_path, "project status"),
    (docs_readme_path, "public docs README"),
    (platform_tour_path, "platform tour"),
    (system_review_path, "system review path"),
    (roadmap_path, "roadmap"),
]:
    text = read(path)
    require("BUSINESS_NOTIFICATION_CHANNELS.md" in text, f"{name} missing notification channel doc link")
    require("businessNotificationChannels" in text, f"{name} missing businessNotificationChannels token")
    require("GET /demo/business-notification-channels" in text, f"{name} missing standalone endpoint")

require("/demo/business-notification-channels" in read(main_path), "API main missing notification demo route")
require(
    "/business-notification-channels/preview" in read(main_path),
    "API main missing notification preview route",
)
require(
    "preview_business_notification_channel_matrix" in read(services_path),
    "services missing notification channel matrix implementation",
)
require(
    "BusinessNotificationChannelMatrixPreviewRead" in read(schemas_path),
    "schemas missing BusinessNotificationChannelMatrixPreviewRead",
)
require(
    "BUSINESS_NOTIFICATION_CHANNELS_PATH" in read(sdk_generator_path),
    "SDK generator missing notification channel endpoint",
)

if sdk_manifest_path.is_file():
    manifest = json.loads(read(sdk_manifest_path))
    notification_manifest = manifest.get("business_notification_channels", {})
    require(
        notification_manifest.get("path") == "/demo/business-notification-channels",
        "SDK manifest notification path mismatch",
    )
    require(
        notification_manifest.get("operation_id")
        == "business_notification_channels_demo_demo_business_notification_channels_get",
        "SDK manifest notification operation id mismatch",
    )
    require(
        "businessNotificationChannels" in manifest.get("required_fields", []),
        "SDK manifest required fields missing businessNotificationChannels",
    )

if is_public_export:
    require(
        "check_public_business_notification_channels.sh" in read(public_smoke_path),
        "public smoke missing business notification channels check",
    )
else:
    require(
        'copy_path "scripts/check_public_business_notification_channels.sh"' in read(export_script_path),
        "export script missing business notification channels checker",
    )
    require(
        "check_public_business_notification_channels.sh" in read(ci_smoke_path),
        "private smoke missing business notification channels checker",
    )
    require(
        "check_public_business_notification_channels.sh" in read(release_gate_path),
        "release gate missing business notification channels checker",
    )

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public business notification channels contract ok")
PY
