# ADR-0062: Public-Safe Observability Proof

## Status

Accepted

## Context

DriveDesk already has public-safe evidence for API health, auth metrics,
integration metrics, SLO canary gates, runtime rollout, and scheduled alerting.
Those pieces prove individual operational surfaces, but the public repository
also needs one cohesive observability proof that connects metrics, logs, alerts,
runbooks, and dashboards.

The public repository must not expose private telemetry, raw logs, runtime
addresses, dashboard screenshots from private systems, credentials, customer
data, or production deployment state.

## Decision

Add a public-safe observability proof:

- `docs/public/OBSERVABILITY_PROOF.md` describes the observability loop;
- `infra/observability/observability-proof.sanitized.json` stores the source
  public-safe evidence snapshot;
- `docs/public/evidence/observability-proof.sanitized.json` mirrors the evidence
  for the public docs surface;
- `scripts/check_public_observability_proof.sh` validates the evidence, docs,
  export wiring, redaction boundary, and CI integration.

The proof uses synthetic data and public-safe signal names only. It models
Prometheus-compatible metrics, Loki-compatible structured logs,
Alertmanager-compatible alerts, and Grafana-compatible dashboards without
publishing private runtime telemetry.

## Consequences

- Reviewers can verify an end-to-end SRE loop from public artifacts.
- Observability is represented as executable evidence, not only prose.
- Public evidence remains sanitized and detached from private infrastructure.
- Future public dashboard examples can build on the same evidence contract.
