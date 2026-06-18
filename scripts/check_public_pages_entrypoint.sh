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


is_public_export = (root / "PUBLIC_EXPORT_MANIFEST.md").is_file()

if is_public_export:
    html = read(index_path)
    require(index_path.is_file(), "missing public Pages root index.html")
    for token in [
        "<!doctype html>",
        "DriveDesk Core",
        "Public Engineering Surface",
        "Review Flow",
        "Architecture Trace",
        "Evidence Matrix",
        "apps/admin/public-demo/",
        "docs/public/SYSTEM_DESIGN.md",
        "docs/public/API_BACKED_DEMO.md",
        "docs/public/SANITIZED_EVIDENCE.md",
        "docs/public/PLATFORM_MATURITY_70.md",
        "docs/public/ENGINEERING_REVIEW_GUIDE.md",
        "docs/public/PROJECT_STATUS.md",
        "docs/public/TECHNICAL_CAPABILITY_MAP.md",
        "docs/public/OBSERVABILITY_PROOF.md",
        "docs/public/ALERT_ROUTING_EVIDENCE.md",
        "docs/public/ENGINEERING_PROOF.md",
        "docs/openapi.json",
        "docs/public/assets/drivedesk-core-demo-overview.png",
        "https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/ci.yml",
        "bash scripts/ci_smoke_public.sh",
        "bash scripts/check_public_pages_entrypoint.sh",
        "bash scripts/check_public_engineering_proof.sh",
    ]:
        require(token in html, f"public Pages index missing {token}")

    for path in [
        "apps/admin/public-demo/index.html",
        "docs/public/SYSTEM_DESIGN.md",
        "docs/public/API_BACKED_DEMO.md",
        "docs/public/SANITIZED_EVIDENCE.md",
        "docs/public/PLATFORM_MATURITY_70.md",
        "docs/public/ENGINEERING_REVIEW_GUIDE.md",
        "docs/public/PROJECT_STATUS.md",
        "docs/public/TECHNICAL_CAPABILITY_MAP.md",
        "docs/public/OBSERVABILITY_PROOF.md",
        "docs/public/ALERT_ROUTING_EVIDENCE.md",
        "docs/public/ENGINEERING_PROOF.md",
        "docs/openapi.json",
        "docs/public/assets/drivedesk-core-demo-overview.png",
    ]:
        require((root / path).exists(), f"public Pages index target missing: {path}")

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
    lowered = html.lower()
    for pattern in private_patterns:
        require(re.search(pattern, lowered) is None, f"runtime marker leaked into Pages index: {pattern}")
else:
    export_script = read(export_script_path)
    require('cat > "$EXPORT_DIR/index.html"' in export_script, "export script does not generate root index.html")
    require("PUBLIC_ROOT_URL" in export_script, "export script missing public root URL")
    require("check_public_pages_entrypoint.sh" in export_script, "export script missing Pages entrypoint check")

    if private_smoke_path.is_file():
        require("check_public_pages_entrypoint.sh" in read(private_smoke_path), "private smoke missing Pages entrypoint check")

    if release_gate_path.is_file():
        gate_text = read(release_gate_path)
        require('"index.html"' in gate_text, "release gate missing root index.html requirement")
        require("check_public_pages_entrypoint.sh" in gate_text, "release gate missing Pages entrypoint check")

if public_smoke_path.is_file():
    require("check_public_pages_entrypoint.sh" in read(public_smoke_path), "public smoke missing Pages entrypoint check")

if errors:
    for error in errors:
        print(f"pages_entrypoint_error={error}", file=sys.stderr)
    raise SystemExit("public Pages entrypoint check failed")

print("public Pages entrypoint check ok")
PY
