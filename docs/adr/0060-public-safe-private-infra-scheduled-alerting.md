# ADR-0060: Public-Safe Private Infrastructure Scheduled Alerting

## Status

Accepted

## Context

DriveDesk already records public-safe recurring scheduled validation evidence.
That proves the validation loop exists, but reviewers also need to see what
happens when the loop fails or goes stale.

The public repository must not expose private infrastructure details, alerting
secrets, notification endpoints, raw logs, request bodies, or production data.

## Decision

Add a public-safe scheduled alerting layer:

- `infra/state-validation/private-infra-scheduled-alerting.sanitized.json`
  records the `scheduled_validation_alerting` model, alert policy, signals,
  notification routes, runbook keys, and redaction boundaries;
- `docs/public/evidence/private-infra-scheduled-alerting.sanitized.json`
  exposes a sanitized reviewer-facing evidence snapshot;
- `.github/workflows/scheduled-validation.yml` emits and uploads a sanitized
  failure artifact only when scheduled validation fails;
- `scripts/check_public_private_infra_scheduled_alerting.sh` validates the
  contract, workflow failure handler, runbook catalog, alert routes, and
  no-mutation boundary.

## Consequences

- Scheduled validation now has a public-safe incident response path.
- Reviewers can see missed-run, failed-run, and secret-boundary alert signals.
- External notifications remain disabled in the public surface because they
  require private credentials and destination details.
- Release promotion is documented as blocked until a fresh validation succeeds
  after a missed or failed scheduled check.
