#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
GITOPS_DIR="${GITOPS_DIR:-"$ROOT/infra/gitops"}"

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

"$PYTHON_BIN" - <<'PY' "$GITOPS_DIR"
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

gitops_dir = Path(sys.argv[1])

required_files = [
    "image-automation/build-artifact.yaml",
    "image-automation/update-proposal.yaml",
    "promotion/image-promotion.yaml",
    "drift/desired-state.yaml",
    "remediation/decision.yaml",
]

missing = [relative for relative in required_files if not (gitops_dir / relative).is_file()]
texts = {
    relative: (gitops_dir / relative).read_text(encoding="utf-8")
    for relative in required_files
    if (gitops_dir / relative).is_file()
}
all_text = "\n".join(texts.values()).lower()

private_markers = [
    "auto" + "school",
    "land" + "vps",
    "duck" + "dns",
    "xr" + "ay",
    "vl" + "ess",
    "reality" + "settings",
    "215" + "689",
]

build_artifact = texts.get("image-automation/build-artifact.yaml", "")
update_proposal = texts.get("image-automation/update-proposal.yaml", "")
promotion = texts.get("promotion/image-promotion.yaml", "")
desired = texts.get("drift/desired-state.yaml", "")
remediation = texts.get("remediation/decision.yaml", "")

candidate_tag = "gitops-candidate-2026-06-18"
image_repository = "ghcr.io/alexgerlitz/drivedesk-core-public"
image_digest = "sha256:7d0d0f3f0c7b0ed1f7b4e1f9c6a3f1d2e8b7c4a5f1e2d3c4b5a6978877665544"
audit_event = "gitops.image_update.proposed"

digest_pattern = re.compile(r"sha256:[a-f0-9]{64}")

checks = {
    "image_automation_files_present": not missing,
    "image_tag_recorded": all(
        candidate_tag in text for text in [build_artifact, update_proposal, promotion, desired]
    ),
    "image_digest_recorded": all(
        image_digest in text for text in [build_artifact, update_proposal]
    )
    and bool(digest_pattern.search(build_artifact))
    and bool(digest_pattern.search(update_proposal)),
    "sbom_attached": "sbomAttached: true" in build_artifact and "sbomFormat: spdx-json" in build_artifact,
    "scanner_recorded": "scanner: trivy" in build_artifact,
    "critical_high_vulnerabilities_zero": all(
        value in build_artifact
        for value in ["criticalVulnerabilities: 0", "highVulnerabilities: 0"]
    ),
    "provenance_attached": "provenanceAttached: true" in build_artifact,
    "update_proposal_recorded": all(
        value in update_proposal
        for value in [
            "kind: ImageUpdateProposal",
            "status: proposed",
            "reviewerRequired: true",
            "promotionFlow: build_to_gitops_to_staged_promotion",
        ]
    ),
    "target_gitops_files_recorded": all(
        value in update_proposal
        for value in [
            "infra/gitops/promotion/image-promotion.yaml",
            "infra/gitops/drift/desired-state.yaml",
        ]
    ),
    "evidence_gates_referenced": all(
        value in update_proposal
        for value in [
            "public_export_secret_scan",
            "public_demo_api_smoke",
            "public_helm_chart_render",
            "public_gitops_layout",
            "public_gitops_promotion_drift",
            "public_gitops_drift_remediation",
        ]
    ),
    "pull_request_only_no_mutation": all(
        value in build_artifact + update_proposal
        for value in [
            "applyMode: pull_request_only",
            "noRegistryMutation: true",
            "noClusterMutation: true",
        ]
    ),
    "audit_event_recorded": audit_event in update_proposal,
    "remediation_flow_linked": "gitops.drift_remediation.planned" in remediation,
    "private_markers_absent": not any(marker in all_text for marker in private_markers),
    "production_data_touched": False,
}

passed = all(value for key, value in checks.items() if key != "production_data_touched")
passed = passed and checks["production_data_touched"] is False

payload = {
    "schema_version": 1,
    "check": "public_gitops_image_automation",
    "data_profile": "synthetic_demo_data",
    "automation_model": "ci_image_build_to_gitops_update_proposal",
    "image": {
        "repository": image_repository,
        "tag": candidate_tag,
        "digest": image_digest,
    },
    "automation": {
        "audit_event": audit_event,
        "apply_mode": "pull_request_only",
        "promotion_flow": "build_to_gitops_to_staged_promotion",
        "reviewer_required": True,
    },
    "checks": checks,
    "redaction": {
        "paths_included": False,
        "hostnames_included": False,
        "addresses_included": False,
        "credentials_included": False,
        "raw_logs_included": False,
        "production_data_included": False,
    },
}

if not passed:
    print(json.dumps(payload, indent=2, sort_keys=True))
    if missing:
        print(f"missing GitOps image automation files: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit("public GitOps image automation check failed")

print(json.dumps(payload, indent=2, sort_keys=True))
print(
    "public GitOps image automation check ok: "
    "tag=gitops-candidate-2026-06-18 mode=pull_request_only"
)
PY
