# ADR-0059: Public-Safe Private Infrastructure Scheduled Validation

Status: accepted

## Context

DriveDesk already records a public-safe operational loop for infrastructure
validation, drift detection, remediation planning, reviewed execution, and
post-remediation drift refresh. That proves the loop can run once, but a
DevOps/platform portfolio project also needs to show how the loop stays alive
over time.

The public repository must still avoid live endpoints, private paths,
credentials, raw logs, request bodies, network addresses, and production data.

## Decision

Add a sanitized scheduled validation evidence layer:

- `infra/state-validation/private-infra-scheduled-validation.sanitized.json`
  records the schedule contract;
- `docs/public/evidence/private-infra-scheduled-validation.sanitized.json`
  records the public-safe evidence snapshot;
- `docs/public/PRIVATE_INFRA_SCHEDULED_VALIDATION.md` explains the workflow;
- `.github/workflows/scheduled-validation.yml` runs the public-safe scheduled
  validation checks on cron and manual dispatch;
- `scripts/check_public_private_infra_scheduled_validation.sh` validates source
  links, workflow schedule shape, sample successful runs, missed-run guard,
  read-only boundaries, redaction, and production-data boundaries.

The evidence is a sanitized validation summary only. It does not make the
public export a source of OpenTofu apply, GitOps sync, runtime mutation, service
restart, production apply, or runtime secrets.

## Consequences

- The public surface now shows that validation is recurring, not one-off.
- Reviewers can see schedule, manual fallback, missed-run guard, and sample
  healthy runs without seeing private runtime details.
- The CI and public release gate can fail if scheduled validation loses its
  workflow, checker, read-only boundary, redaction, or production-data
  boundary.
