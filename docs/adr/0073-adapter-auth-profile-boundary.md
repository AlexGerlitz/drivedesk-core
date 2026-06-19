# ADR-0073: Adapter Auth Profile Boundary

## Status

Accepted

## Context

DriveDesk is moving from synthetic public-safe adapters toward future real
provider connectors for systems such as Bitrix24, banks, accounting tools, KKT,
webhooks, and file imports.

The public repository must not contain real credentials, provider endpoints,
tenant subdomains, OAuth tokens, webhook secrets, raw provider payloads, or
external writes. At the same time, the runtime adapter catalog should show how a
real authenticated connector will be wired later, otherwise the catalog only
proves mock execution and not the provider security boundary.

## Decision

Add an `auth_profile` to runtime adapter descriptors.

The profile is public-safe metadata. It describes:

- adapter auth mode;
- whether the public demo requires a secret;
- whether a real provider connector requires a secret;
- symbolic secret reference names;
- where credentials must be placed;
- where token exchange may happen;
- whether external token exchange is allowed;
- data-boundary rules such as `no_public_secrets`,
  `no_browser_token_storage`, and `server_side_provider_calls_only`.

For `crm.bitrix24.mock`, the profile uses:

```json
{
  "mode": "oauth2_or_webhook_boundary",
  "public_demo_requires_secret": false,
  "real_provider_requires_secret": true,
  "secret_refs": ["BITRIX24_WEBHOOK_URL", "BITRIX24_CLIENT_SECRET"],
  "credential_placement": "server_secret_store",
  "token_exchange": "private_connector_only",
  "external_token_exchange": false,
  "data_boundaries": [
    "no_public_secrets",
    "no_browser_token_storage",
    "server_side_provider_calls_only"
  ]
}
```

## Consequences

- `GET /integration-adapters` can explain the secret boundary without exposing
  any secret value.
- `GET /demo/public` can render adapter auth metadata in the public demo.
- Public checks can prove that mock adapters stay secret-free while future real
  providers are modeled as server-side connector work.
- Browser code must not store provider OAuth tokens or webhook secrets.
- Real provider connectors remain private implementation work behind server-side
  secret storage and connector code.

## Verification

```bash
.venv/bin/pytest tests/test_drivedesk_foundation.py::test_adapter_catalog_describes_runtime_adapters tests/test_drivedesk_foundation.py::test_adapter_connection_diagnostics_are_safe_and_operation_aware tests/test_drivedesk_foundation.py::test_api_integration_adapter_catalog_endpoint -q
.venv/bin/pytest tests/test_public_demo_surface.py -q
bash scripts/check_public_demo_api.sh
PREVIEW_ONLY=1 bash scripts/export_public_repo.sh
```
