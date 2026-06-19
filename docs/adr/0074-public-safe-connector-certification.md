# ADR-0074: Public-Safe Connector Certification

Status: accepted

## Context

DriveDesk is moving from one-off integrations toward a provider-neutral
Integration Hub. The public repository already shows runtime adapter catalog,
provider connector guidance, adapter developer flow, auth profiles, operation
contracts, outbox, diagnostics, reconciliation, and incident evidence.

The missing step is a repeatable certification path that explains how a new
external system becomes a connector without exposing provider credentials,
tenant data, raw payloads, private endpoints, or live provider calls.

## Decision

Add a public-safe Connector Certification Path.

Every future connector should pass these stages before real private provider
implementation:

- provider profile;
- capability manifest;
- contract fixtures;
- local certification gate;
- runtime readiness review;
- release proof.

The public proof is represented by:

- `docs/public/CONNECTOR_CERTIFICATION.md`;
- `docs/public/evidence/connector-certification.sanitized.json`;
- `scripts/check_public_connector_certification.sh`;
- public export and release gate coverage.

## Consequences

- A reviewer can see how DriveDesk adds CRM, bank, accounting, ERP, KKT,
  webhook, file, email, telephony, or custom API providers through one
  connector lifecycle.
- Public GitHub Pages can show the connector architecture without secrets.
- Private provider work can start from a stable contract and add real provider
  clients later.
- Connector readiness is not limited to a successful HTTP response; it includes
  auth boundary, outbox, retry, dead-letter, diagnostics, reconciliation,
  incidents, operator review, evidence, and release gates.
