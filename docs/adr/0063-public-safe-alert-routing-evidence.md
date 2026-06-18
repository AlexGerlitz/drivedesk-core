# ADR-0063: Public-Safe Alert Routing Evidence

Status: accepted

## Context

The public observability proof records metrics, logs, alerts, runbooks, and
dashboard panels. That proves the signals exist, but it does not fully show how
an operational alert becomes an actionable incident path.

## Decision

Add a public-safe alert-routing evidence layer:

- sanitized routing contract in `infra/observability/alert-routing.sanitized.json`;
- matching public evidence in `docs/public/evidence/alert-routing.sanitized.json`;
- public explanation in `docs/public/ALERT_ROUTING_EVIDENCE.md`;
- executable verifier in `scripts/check_public_alert_routing.sh`.

The routing contract records route matchers, receivers, grouping, repeat
intervals, escalation, runbook bindings, silence requirements, and failure
artifact references.

## Consequences

- The public repository can prove the alert flow without exposing private
  destinations, secrets, raw logs, payload bodies, runtime addresses, or
  customer data.
- Observability evidence now covers signal creation and incident routing.
- Public export, CI smoke, and release gate must validate the routing evidence.
