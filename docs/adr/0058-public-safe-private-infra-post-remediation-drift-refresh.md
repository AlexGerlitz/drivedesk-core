# ADR-0058: Public-Safe Private Infrastructure Post-Remediation Drift Refresh

Status: accepted

## Context

DriveDesk already records public-safe evidence for infrastructure drift,
private infrastructure validation, remediation planning, and reviewed
remediation execution. The remaining gap is the evidence step after execution:
prove that drift was refreshed again, resolved components are recorded, and any
remaining drift would become an explicit decision instead of an assumption.

The public repository must still avoid live endpoints, private paths,
credentials, raw logs, request bodies, network addresses, and production data.

## Decision

Add a sanitized post-remediation drift refresh evidence layer:

- `infra/state-remediation/private-infra-post-remediation-drift-refresh.sanitized.json`
  records the read-only refresh contract;
- `docs/public/evidence/private-infra-post-remediation-drift-refresh.sanitized.json`
  records the public-safe evidence snapshot;
- `docs/public/PRIVATE_INFRA_POST_REMEDIATION_DRIFT_REFRESH.md` explains the
  workflow;
- `scripts/check_public_private_infra_post_remediation_drift_refresh.sh`
  validates source links, resolved components, residual drift state, read-only
  boundaries, redaction, and production-data boundaries.

The evidence is a sanitized private staging summary only. It does not make the
public export a source of OpenTofu apply, GitOps sync, runtime mutation, service
restart, production apply, or runtime secrets.

## Consequences

- The public surface now shows a closed operational response chain:
  validation -> drift -> remediation plan -> reviewed execution -> drift
  refresh -> clean decision.
- Reviewers can see that remediation was followed by verification, not just a
  declared fix.
- The CI and public release gate can fail if the refresh evidence loses source
  links, resolved-component proof, read-only boundaries, redaction, or
  production-data boundaries.
