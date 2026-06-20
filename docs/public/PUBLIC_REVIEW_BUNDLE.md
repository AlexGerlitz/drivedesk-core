# Public Review Bundle

This is the shortest one-command review path for DriveDesk Core. It is intended
for a technical reader who wants to verify the public engineering surface before
opening the full documentation set.

## One Command

```bash
bash scripts/run_public_review_bundle.sh
```

The command checks the public entrypoint, system review path, Business OS tour,
quickstart, Review Console, verification matrix, project status, capability map,
evidence index, demo health, OpenAPI drift, demo API, SDK, observability, alert
routing, and proof contract.

## What This Proves

| Area | Evidence | Verifier |
| --- | --- | --- |
| Public entrypoint | `index.html`, `docs/public/SYSTEM_REVIEW_PATH.md` | `bash scripts/check_public_pages_entrypoint.sh` |
| Review route | `docs/public/REVIEWER_QUICKSTART.md`, `docs/public/ENGINEERING_REVIEW_GUIDE.md` | `bash scripts/check_public_reviewer_quickstart.sh` |
| Review Console | `docs/public/REVIEW_CONSOLE.md`, `docs/public/evidence/review-console.sanitized.json` | `bash scripts/check_public_review_console.sh` |
| Claim-to-evidence map | `docs/public/PUBLIC_VERIFICATION_MATRIX.md`, `docs/public/TECHNICAL_CAPABILITY_MAP.md` | `bash scripts/check_public_verification_matrix.sh` |
| Evidence contract | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json` | `bash scripts/check_public_evidence_index.sh` |
| Demo and API | `docs/public/PUBLIC_DEMO_HEALTH.md`, `docs/openapi.json`, `sdk/generated/public-demo/` | `bash scripts/check_public_demo_health.sh` |
| Operations proof | `docs/public/OBSERVABILITY_PROOF.md`, `docs/public/ALERT_ROUTING_EVIDENCE.md`, `docs/public/ENGINEERING_PROOF.md` | `bash scripts/check_public_engineering_proof.sh` |

## Machine-Readable Evidence

```text
docs/public/evidence/public-review-bundle.sanitized.json
```

This file records the review bundle command, included checks, review documents,
pass signals, and public-safe boundary flags.

## Self-Check

```bash
bash scripts/check_public_review_bundle.sh
```

The self-check validates that this document, the sanitized evidence file, the
runner, public smoke path, export script, evidence index, generated public
README, and Pages entrypoint stay connected.

## Boundary

The bundle uses synthetic data and sanitized evidence only. It does not require
production data, credentials, private runtime addresses, raw logs, customer
records, provider secrets, or private deployment state.
