# ADR-0075: Public-Safe Connector Fixture Replay

## Status

Accepted

## Context

DriveDesk Core exposes a public connector certification path for future CRM,
bank, accounting, ERP, KKT, webhook, file, email, telephony, and custom API
providers.

The certification path requires contract fixtures, but a useful public evidence
surface needs a repeatable replay contract, not only a checklist. Reviewers
should be able to verify that synthetic provider payloads cover happy-path
normalization, redaction, validation failure, retry, dead-letter, and
reconciliation behavior.

The public repository must not include real provider credentials, raw request
bodies, tenant endpoints, customer data, production logs, or live external
calls.

## Decision

Add a public-safe connector fixture replay layer:

- `docs/public/CONNECTOR_FIXTURE_REPLAY.md`;
- `examples/connector-fixtures/replay-fixtures.sanitized.json`;
- `docs/public/evidence/connector-fixture-replay.sanitized.json`;
- `scripts/check_public_connector_fixture_replay.sh`.

The replay layer validates only synthetic descriptors and sanitized outcomes. It
checks required fixture groups, redaction flags, routing outcomes, evidence
index coverage, public export coverage, and release-gate coverage.

## Consequences

- Connector certification becomes more executable and easier to review.
- Future private connectors can reuse the same fixture groups as regression
  scenarios.
- Public evidence stays safe because it records shape and expected behavior, not
  real payloads or credentials.
- A new connector is not considered fixture-ready until the replay checker
  passes.
