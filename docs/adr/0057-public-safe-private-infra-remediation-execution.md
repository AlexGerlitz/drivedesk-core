# ADR-0057: Public-Safe Private Infrastructure Remediation Execution Evidence

Status: accepted

## Context

DriveDesk already records public-safe evidence for infrastructure drift,
private infrastructure validation, and remediation planning. That proves the
system can detect drift and build a reviewed plan, but the public engineering
surface also needs to show the next operational step: controlled execution and
post-remediation verification.

The public repository must still avoid live endpoints, private paths,
credentials, raw logs, request bodies, network addresses, and production data.

## Decision

Add a sanitized private remediation execution evidence layer:

- `infra/state-remediation/private-infra-remediation-execution.sanitized.json`
  records the reviewed execution contract;
- `docs/public/evidence/private-infra-remediation-execution.sanitized.json`
  records the public-safe evidence snapshot;
- `docs/public/PRIVATE_INFRA_REMEDIATION_EXECUTION.md` explains the workflow;
- `scripts/check_public_private_infra_remediation_execution.sh` validates the
  evidence, redaction boundary, source links, preflight gates, postchecks, and
  rollback context.

The evidence records private staging execution summary only. It does not make
public export a source of infrastructure apply, production apply, cluster
mutation, or runtime secrets.

## Consequences

- The public surface now shows a full operational response chain:
  validation -> drift -> remediation plan -> reviewed execution -> postchecks.
- Reviewers can inspect machine-readable evidence without seeing private
  runtime details.
- The CI and public release gate can fail if the execution evidence loses
  review, rollback, postcheck, redaction, or production-data boundaries.
