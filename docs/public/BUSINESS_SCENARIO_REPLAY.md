# Business Scenario Replay

DriveDesk is designed as a business operating system: external systems provide
signals, DriveDesk normalizes them into business facts, detects risk, and gives
the operator a safe action plan.

The Business Scenario Replay is the public-safe contract for that idea. It uses
synthetic data only and shows how the same core can support CRM, bank,
accounting, support, telephony, supplier, inventory, and procurement-style
signals without making real provider calls.

Document path: `docs/public/BUSINESS_SCENARIO_REPLAY.md`.

## Contract

The replay is exposed in two places:

```text
GET /demo/public -> businessScenarioReplay
GET /demo/business-scenario-replay
```

The standalone endpoint returns the same `businessScenarioReplay` contract as
the full public demo payload. The Control Tower tab renders the same data from
the static fallback and from the API-backed mode.

## Replay Paths

| Scenario | External signals | DriveDesk decision | Safe action boundary |
| --- | --- | --- | --- |
| `crm-bank-payment-mismatch` | CRM deal, bank statement, accounting export | Open reconciliation workbench | Internal exception can be created automatically; accounting export and customer message require approval. |
| `support-sla-risk` | Support inbox, telephony callback, SLA policy | Escalate before SLA breach | Internal escalation can be created automatically; callback and outbound message remain draft-only. |
| `procurement-delay-risk` | Supplier portal, inventory stock, bank payment order | Create procurement exception and check cash timing | Manager task can be created automatically; bank payment release is blocked until approval. |

## Flow

```text
external signal
  -> safe normalization
  -> cross-system detection
  -> workbench context
  -> recommended action plan
  -> approval-gated execution
```

The replay intentionally separates internal actions from external writes:

- internal records, tasks, and exceptions can be safe automation candidates;
- customer messages, callbacks, accounting exports, and bank/payment actions
  stay behind approval;
- raw provider payloads, credentials, message bodies, phone numbers, and
  provider-specific secrets are not returned by the public contract.

## Evidence

Verifier:

```bash
bash scripts/check_public_business_scenario_replay.sh
```

Related evidence:

- `docs/public/BUSINESS_CONTROL_TOWER.md`
- `docs/public/API_BACKED_DEMO.md`
- `docs/public/TECHNICAL_CAPABILITY_MAP.md`
- `apps/admin/public-demo/index.html`
- `docs/openapi.json`

## Why It Matters

This is the product-level proof that DriveDesk is not limited to one vertical.
The same pattern can model different businesses:

1. collect external state from adapters;
2. normalize it into a common business fact model;
3. detect mismatch, delay, SLA, cash, or operational risk;
4. build context for the right role;
5. propose actions while keeping risky external writes behind approval.
