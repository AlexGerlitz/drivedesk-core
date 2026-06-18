# Public Evidence Index

This document is the human-readable entrypoint for the DriveDesk Core public
evidence index.

The machine-readable index lives at:

```text
docs/public/evidence/public-evidence-index.sanitized.json
```

The index connects public capabilities to:

- the document that explains the capability;
- the sanitized evidence files that support it;
- the executable verifier commands;
- the public URL or relative path that exposes the artifact;
- the public/private boundary for that evidence group.

## Why This Exists

The public repository contains many checked artifacts: API contract, generated
SDK, recovery drills, release gates, GitOps, OpenTofu, observability, alerting,
incident response, and scheduled validation evidence.

The evidence index keeps those artifacts tied together as one contract instead
of a loose collection of notes. It is useful for release review, public export
validation, and future automation that needs to discover proof artifacts without
parsing Markdown by hand.

## Indexed Capability Groups

| Capability group | Primary doc | Verifier |
| --- | --- | --- |
| Public engineering entrypoint | `docs/public/REVIEWER_QUICKSTART.md` | `bash scripts/check_public_reviewer_quickstart.sh` |
| API and SDK | `docs/public/API_BACKED_DEMO.md` | `bash scripts/check_public_demo_api.sh` |
| Core domain | `docs/public/SYSTEM_DESIGN.md` | `bash scripts/ci_smoke_public.sh` |
| Integration hub | `docs/public/INTEGRATION_ADAPTER_CATALOG.md` | `bash scripts/check_public_demo_api.sh` |
| Observability | `docs/public/OBSERVABILITY_PROOF.md` | `bash scripts/check_public_observability_proof.sh` |
| Alert routing | `docs/public/ALERT_ROUTING_EVIDENCE.md` | `bash scripts/check_public_alert_routing.sh` |
| Incident response | `docs/public/INCIDENT_RESPONSE_DEMO.md` | `bash scripts/check_public_engineering_proof.sh` |
| Release safety | `docs/public/RELEASE_ROLLBACK_EVIDENCE.md` | `bash scripts/check_public_release_rollback.sh` |
| GitOps and IaC | `docs/public/GITOPS_DELIVERY.md` | `bash scripts/check_public_gitops_layout.sh` |
| Private staging validation | `docs/public/PRIVATE_INFRA_VALIDATION.md` | `bash scripts/check_public_private_infra_validation.sh` |
| Scheduled validation | `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md` | `bash scripts/check_public_private_infra_scheduled_validation.sh` |
| Platform maturity | `docs/public/PLATFORM_MATURITY_70.md` | `bash scripts/check_public_platform_maturity_70.sh` |

## Boundary

The evidence index is public-safe. It references synthetic data and sanitized
evidence only. It does not include private runtime addresses, credentials, raw
logs, request bodies, customer data, provider secrets, or live infrastructure
state.

## Verification

```bash
bash scripts/check_public_evidence_index.sh
```

The check validates that:

- every indexed public document exists;
- every indexed evidence file exists;
- every indexed verifier command is present;
- every verifier referenced by the index is part of the public smoke path;
- public URLs are relative paths or the configured GitHub Pages root;
- redaction flags stay public-safe;
- the public README, review guide, status page, capability map, proof contract,
  sanitized evidence page, root Pages entrypoint, export script, release gate,
  and smoke scripts reference the evidence index.
