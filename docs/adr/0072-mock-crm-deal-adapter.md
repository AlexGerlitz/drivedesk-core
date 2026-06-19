# ADR-0072: Mock CRM Deal Adapter

## Status

Accepted

## Context

DriveDesk needs to prove that external business systems can feed the platform
without becoming the operational center. The business control tower already
uses `crm.bitrix24.mock` as the source for provider intake, workbench context,
payment mismatch detection, action planning, and notification previews.

Before real Bitrix24, bank, accounting, or support credentials are configured,
the runtime catalog still needs an executable CRM adapter contract. Otherwise
the public surface can describe CRM intake, but the worker/runtime adapter layer
cannot prove it.

## Decision

Add `crm.bitrix24.mock` as an executable public-safe runtime adapter.

The adapter:

- supports tenant-owned connection profiles;
- declares `crm:deal.preview` and `crm:deal.ingest` scopes;
- exposes `crm_deal_intake_preview` for provider intake preview;
- exposes `crm_deal_ingest_execute` for retryable outbox-backed ingestion;
- accepts synthetic CRM deal batches;
- supports field mapping from provider-shaped keys such as `ID` and
  `STAGE_ID`;
- returns only safe normalized summaries, amount buckets, source states,
  accepted subject references, and dropped sensitive key names;
- does not return raw payload values, credentials, phone numbers, names,
  emails, addresses, passport data, tokens, or secrets.

## Consequences

- `GET /integration-adapters` now includes a CRM adapter contract alongside
  file import, accounting export, and internal noop adapters.
- The public demo can show a real runtime catalog entry for CRM intake instead
  of treating CRM as a future-only provider.
- The business control tower flow now connects:

```text
CRM adapter contract
  -> provider intake preview
  -> normalized observation
  -> workbench context
  -> detection
  -> action plan
  -> notification preview
  -> approval-gated dry-run repair
```

- Real Bitrix24 integration remains a private/provider-specific layer to be
  added later. OAuth tokens, webhook secrets, tenant subdomains, real payloads,
  and external writes stay outside the public repository and public demo.

## Verification

```bash
.venv/bin/pytest tests/test_drivedesk_foundation.py::test_mock_crm_deal_adapter_contract -q
.venv/bin/pytest tests/test_public_demo_surface.py::test_public_demo_data_is_synthetic_and_product_shaped -q
bash scripts/check_public_demo_api.sh
```
