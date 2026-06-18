# ADR-0055: Public-Safe Private Infrastructure Validation

Status: accepted

## Context

DriveDesk has public-safe evidence for OpenTofu plans, desired-vs-observed
state drift, private staging runtime rollout, and GitOps delivery. The next
DevOps layer needs to show how real private staging/control-plane state is
validated before any apply, deploy, or remediation decision.

The public repository must not expose private hostnames, network addresses,
server paths, credentials, raw logs, request bodies, or production data.

## Decision

Add a public-safe private infrastructure validation layer:

```text
infra/state-validation/private-infra-validation.sanitized.json
docs/public/evidence/private-infra-validation.sanitized.json
docs/public/PRIVATE_INFRA_VALIDATION.md
scripts/check_public_private_infra_validation.sh
```

The layer records a read-only collector boundary, references the public-safe
OpenTofu, drift, runtime rollout, GitOps, and staging evidence contracts, and
emits a machine-readable validation payload.

## Consequences

- Private staging state validation becomes part of the public DevOps story.
- Public evidence proves the validation boundary without publishing live
  infrastructure details.
- No public artifact performs infrastructure apply, runtime restart, or cluster
  mutation.
- Remediation remains an operator-reviewed decision.
