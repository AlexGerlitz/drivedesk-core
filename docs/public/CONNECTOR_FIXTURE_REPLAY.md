# Connector Fixture Replay

This document defines the public-safe replay layer for connector certification.
It turns the fixture requirement from `CONNECTOR_CERTIFICATION.md` into a
repeatable check that can run without real provider credentials or external
calls.

The replay layer is intentionally synthetic. It proves connector behavior
shape, not real provider access.

```text
provider fixture
  -> contract validation
  -> safe normalization
  -> sensitive-field redaction
  -> retry/dead-letter classification
  -> reconciliation result
  -> sanitized evidence
```

## Goal

A provider connector is not ready because it has an API client. It is ready only
when its expected payload behavior can be replayed and checked.

The public replay layer proves:

- safe payloads normalize into DriveDesk fields;
- raw payloads and credentials are not returned;
- sensitive fields are dropped before public evidence is produced;
- invalid payloads stop before outbox work is created;
- temporary failures become retry work;
- terminal failures become dead-letter/operator review work;
- reconciliation mismatches are represented without leaking provider data.

## Replay Fixtures

The public fixture file is:

```text
examples/connector-fixtures/replay-fixtures.sanitized.json
```

It contains only synthetic fixture descriptors. It does not contain real request
bodies, tokens, provider endpoints, customer records, phone numbers, email
addresses, names, or tenant identifiers.

Required fixture groups:

| Fixture group | Expected behavior |
| --- | --- |
| `happy_path_preview` | A safe CRM-style provider payload normalizes into a preview result. |
| `sensitive_payload_redaction` | Sensitive keys are dropped and public evidence keeps only redaction metadata. |
| `invalid_payload` | Validation errors are returned and no outbox event is created. |
| `retryable_provider_failure` | Temporary provider failure is classified for retry. |
| `dead_letter_provider_failure` | Terminal or exhausted work creates operator review. |
| `reconciliation_mismatch` | Provider-vs-DriveDesk mismatch is represented through sanitized evidence. |

## Replay Contract

Every fixture must expose:

| Field | Meaning |
| --- | --- |
| `group` | One of the required replay groups. |
| `provider_key` | Public-safe provider identifier such as `crm.demo.mock`. |
| `provider_class` | Provider class such as `crm`, `bank`, or `accounting_or_erp`. |
| `stage` | Replay stage: `preview`, `redaction`, `validation`, `retry`, `dead_letter`, or `reconciliation`. |
| `input_profile` | The safe shape of the input, not the raw input body. |
| `expected_result` | Expected public-safe outcome and routing behavior. |

The expected result must keep these public boundaries:

```text
raw_payload_returned=false
credentials_returned=false
external_call_made=false
public_demo_persistence=false
safe_payload_present=true
```

## Replay Outcomes

| Fixture group | Public outcome |
| --- | --- |
| `happy_path_preview` | `safe_payload_present=true`, `raw_payload_returned=false`, and no external provider call. |
| `sensitive_payload_redaction` | `redaction_evidence_present=true` and dropped keys include tokens, names, phones, emails, addresses, and raw request bodies. |
| `invalid_payload` | `validation_errors` is non-empty and `outbox_event_created=false`. |
| `retryable_provider_failure` | `retryable=true`, `dead_letter=false`, and `next_state=retry_scheduled`. |
| `dead_letter_provider_failure` | `dead_letter=true`, `operator_review=true`, and event `integration.operator_review.created` is emitted. |
| `reconciliation_mismatch` | `drivedesk_integration_reconciliations` records a mismatch with safe references only. |

## Evidence

The machine-readable public evidence is:

```text
docs/public/evidence/connector-fixture-replay.sanitized.json
```

It binds the fixture file, the replay document, the verifier command, and the
certification path.

The verifier is:

```bash
bash scripts/check_public_connector_fixture_replay.sh
```

## Public Demo Contract

The replay is also exposed in the public-safe demo payload as
`connectorFixtureReplay`, and as a standalone read-only endpoint for SDK and
reviewer checks.

```text
GET /demo/public
  -> connectorFixtureReplay.summary
  -> connectorFixtureReplay.outcomes
  -> connectorFixtureReplay.boundaries
  -> connectorFixtureReplay.docs

GET /demo/connector-fixture-replay
  -> summary
  -> outcomes
  -> boundaries
  -> docs
```

The GitHub Pages shell renders the same data in the Integrations tab through
`connectorReplaySummaryRows`, `connectorReplayOutcomeRows`,
`connectorReplayBoundaryRows`, and `connectorReplayDocRows`.

The check validates:

- this document;
- the sanitized replay evidence file;
- the sanitized fixture file;
- every required fixture group and expected outcome;
- private-marker redaction;
- cross-links from connector certification, provider guide, adapter developer
  guide, adapter catalog, operation contracts, Platform Tour, API demo notes,
  Project Status, Technical Capability Map, Roadmap, README, and Evidence
  Index;
- private and public smoke path coverage;
- public export manifest and release gate coverage.

## Relationship To Certification

`CONNECTOR_CERTIFICATION.md` defines the path. This document makes the fixture
stage executable:

```text
contract_fixtures
  -> connector fixture replay
  -> fixtures_ready
  -> public_gate_passed
```

Private connector code may later replace synthetic fixture input with provider
client calls, but the replay expectations stay useful as regression tests.

## Boundary

The replay layer is public-safe. It uses synthetic descriptors and sanitized
evidence only. It does not contain provider tokens, raw request bodies, real
tenant data, customer records, live endpoints, browser tokens, or external
provider calls.
