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

import sys
from pathlib import Path

root = Path(sys.argv[1])
guide_path = root / "docs/public/PROVIDER_CONNECTOR_GUIDE.md"
readme_path = root / "docs/public/README.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
roadmap_path = root / "docs/public/ROADMAP.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
adapter_catalog_path = root / "docs/public/INTEGRATION_ADAPTER_CATALOG.md"
api_demo_path = root / "docs/public/API_BACKED_DEMO.md"
release_gate_path = root / "scripts/public_repo_release_gate.sh"
export_script_path = root / "scripts/export_public_repo.sh"
public_smoke_path = root / "scripts/ci_smoke_public.sh"
is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

errors: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


require(guide_path.is_file(), "missing docs/public/PROVIDER_CONNECTOR_GUIDE.md")
guide = read(guide_path)

for token in [
    "Provider Connector Guide",
    "GET /integration-adapters",
    "auth_profile",
    "oauth2_or_webhook_boundary",
    "server_secret_store",
    "private_connector_only",
    "no_browser_token_storage",
    "crm.bitrix24.mock",
    "accounting.export.mock",
    "file.import.fake",
    "business-provider-intake/preview",
    "business-workbench-context/preview",
    "integration.crm_deal.ingest.requested",
    "accounting.export.requested",
    "drivedesk_integration_connection_checks",
    "drivedesk_integration_reconciliations",
    "drivedesk_integration_incidents",
    "integration.operator_review.created",
    "check_public_provider_connector_guide.sh",
    "check_public_demo_api.sh",
    "check_public_business_control_tower.sh",
]:
    require(token in guide, f"provider connector guide missing {token}")

for path, label in [
    (readme_path, "docs/public README"),
    (status_path, "project status"),
    (roadmap_path, "roadmap"),
    (capability_map_path, "technical capability map"),
    (adapter_catalog_path, "adapter catalog"),
    (api_demo_path, "API-backed demo docs"),
]:
    text = read(path)
    require("PROVIDER_CONNECTOR_GUIDE.md" in text, f"{label} missing provider connector guide link")

if is_public_export:
    require(public_smoke_path.is_file(), "public smoke missing in public export")
    require(
        "check_public_provider_connector_guide.sh" in read(public_smoke_path),
        "public smoke missing provider guide checker",
    )
else:
    release_gate = read(release_gate_path)
    require("docs/public/PROVIDER_CONNECTOR_GUIDE.md" in release_gate, "release gate missing provider guide file check")
    require("missing provider connector guide" in release_gate, "release gate missing provider guide error")
    require("check_public_provider_connector_guide.sh" in release_gate, "release gate missing provider guide script check")

    export_script = read(export_script_path)
    require("check_public_provider_connector_guide.sh" in export_script, "export script missing provider guide checker")
    require("public provider connector guide" in export_script, "export manifest missing provider guide")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("public provider connector guide check ok")
PY
