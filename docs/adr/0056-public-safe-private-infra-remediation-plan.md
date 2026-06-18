# ADR-0056: Public-Safe Private Infrastructure Remediation Plan

Status: accepted

## Context

DriveDesk has public-safe evidence for OpenTofu plans, infrastructure drift,
GitOps drift remediation, private staging rollout, and read-only private
infrastructure validation. The next DevOps question is:

What happens after read-only validation detects drift?

The public repository must not expose private hostnames, network addresses,
server paths, credentials, raw logs, request bodies, or production data. It also
must not apply infrastructure or mutate private runtime from public artifacts.

## Decision

Add a public-safe private infrastructure remediation planning layer:

```text
infra/state-remediation/private-infra-remediation-plan.sanitized.json
docs/public/evidence/private-infra-remediation-plan.sanitized.json
docs/public/PRIVATE_INFRA_REMEDIATION.md
scripts/check_public_private_infra_remediation.sh
```

The layer carries forward read-only validation and drift evidence into a
plan-only remediation decision. It records drifted components, preflight gates,
postcheck gates, rollback context, operator review, and no public apply.

## Consequences

- The public project now shows the operational step after drift detection.
- Remediation remains reviewed and plan-only until a private operator applies
  it through the private control plane.
- Public evidence proves the remediation shape without publishing live
  infrastructure details.
- No public artifact performs infrastructure apply, service restart, or cluster
  mutation.
