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

import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
tour_path = root / "docs/public/PLATFORM_TOUR.md"
demo_data_path = root / "apps/admin/public-demo/demo-data.js"
demo_index_path = root / "apps/admin/public-demo/index.html"
api_doc_path = root / "docs/public/API_BACKED_DEMO.md"
sdk_doc_path = root / "docs/public/CLIENT_SDK.md"
status_path = root / "docs/public/PROJECT_STATUS.md"
capability_map_path = root / "docs/public/TECHNICAL_CAPABILITY_MAP.md"
docs_readme_path = root / "docs/public/README.md"
root_readme_path = root / "README.md"
root_index_path = root / "index.html"
export_script_path = root / "scripts/export_public_repo.sh"
private_smoke_path = root / "scripts/ci_smoke.sh"
release_gate_path = root / "scripts/public_repo_release_gate.sh"

errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


require(tour_path.is_file(), "missing docs/public/PLATFORM_TOUR.md")
text = read(tour_path)

for token in [
    "DriveDesk Platform Tour",
    "Product Path",
    "Demo Route",
    "Architecture Trace",
    "Verification",
    "Boundary",
    "businessControlTower.providerIntake",
    "businessControlTower.workbenchContext",
    "workflowScenarios",
    "adapterStudio",
    "sdk/generated/public-demo/",
    "worker:drivedesk_worker.main.process_pending_outbox",
    "alertRouting",
    "incidentResponse",
    "engineeringProof",
    "EVIDENCE_INDEX.md",
    "Control Tower",
    "Integrations",
    "Operations",
    "Incidents",
    "Proof",
    "server_secret_store",
    "private_connector_only",
    "no_browser_token_storage",
    "executionMode: contract_only",
    "safeToRunAgainstPublicDemo: false",
    "bash scripts/check_public_platform_tour.sh",
    "bash scripts/check_public_demo_api.sh",
    "bash scripts/check_public_demo_sdk.sh",
    "bash scripts/check_public_business_control_tower.sh",
    "bash scripts/check_public_engineering_proof.sh",
]:
    require(token in text, f"platform tour missing {token}")

for path, tokens in {
    demo_data_path: ["adapterStudio", "businessControlTower", "incidentResponse", "engineeringProof"],
    demo_index_path: ["Adapter Studio", "Control Tower", "Operations", "Incidents", "Proof"],
    api_doc_path: ["adapterStudio", "businessControlTower", "engineeringProof"],
    sdk_doc_path: ["adapterStudio", "contract_only", "safeToRunAgainstPublicDemo"],
    status_path: ["PLATFORM_TOUR.md", "Adapter Studio", "Business control tower"],
    capability_map_path: ["PLATFORM_TOUR.md", "Integration adapter model", "Business operations control tower"],
    docs_readme_path: ["PLATFORM_TOUR.md", "DriveDesk Platform Tour"],
}.items():
    body = read(path)
    require(body, f"missing required file: {path.relative_to(root)}")
    for token in tokens:
        require(token in body, f"{path.relative_to(root)} missing {token}")

is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()
if is_public_export:
    root_readme = read(root_readme_path)
    index = read(root_index_path)
    for token in [
        "PLATFORM_TOUR.md",
        "Business OS tour",
        "Adapter Studio",
        "Control Tower",
        "business event -> workflow -> adapter -> incident -> proof",
    ]:
        require(token in root_readme, f"public README missing {token}")
        require(token in index, f"public index missing {token}")
else:
    export_script = read(export_script_path)
    private_smoke = read(private_smoke_path)
    release_gate = read(release_gate_path)
    for token in [
        "PLATFORM_TOUR.md",
        "Business OS tour",
        "Adapter Studio",
        "business event -> workflow -> adapter -> incident -> proof",
        "check_public_platform_tour.sh",
    ]:
        require(token in export_script, f"export script missing {token}")
    require("check_public_platform_tour.sh" in private_smoke, "private smoke missing platform tour check")
    require("check_public_platform_tour.sh" in release_gate, "release gate missing platform tour check")

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
lowered = text.lower()
for pattern in private_patterns:
    require(re.search(pattern, lowered) is None, f"runtime marker leaked into platform tour: {pattern}")

if errors:
    for error in errors:
        print(f"platform_tour_error={error}", file=sys.stderr)
    raise SystemExit("public platform tour check failed")

print("public platform tour check ok")
PY
