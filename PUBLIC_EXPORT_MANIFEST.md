# Public Export Manifest

Generated at: 2026-06-17T23:18:16Z
Source snapshot: private repository clean export

Copied public-safe areas:

- apps/api
- apps/worker
- apps/admin
- packages/core
- infra/docker
- examples
- tests/test_drivedesk_foundation.py
- tests/test_drivedesk_core_api.py
- tests/test_public_demo_surface.py
- selected docs and ADRs
- generated docs/openapi.json
- generated public demo SDK
- static public demo shell
- public demo screenshot
- public demo health workflow
- public system design overview
- public API-backed demo overview
- public workflow demo overview
- public generated SDK overview
- public integration adapters overview
- public runtime adapter catalog endpoint: /integration-adapters
- public runtime adapter catalog doc
- public demo adapter connectionProfileSupported metadata
- public integration mapping validation doc
- public integration mapping transform doc
- public integration connection scopes doc
- public demo adapter requiredMappingKeys metadata
- public demo adapter supportedConnectionScopes metadata
- public integration observability overview
- public roadmap
- public demo integration health surface
- public demo API-backed loading surface
- public demo synthetic business workflow surface
- public demo generated OpenAPI SDK
- public platform-admin control-plane surface
- public session revocation control-plane surface
- public business record tenant-owned surface
- public business record lifecycle and metrics surface
- public business record outbox adapter key: internal.business_record
- public workflow rule tenant-owned automation surface
- public workflow rule audit and outbox surface
- public workflow rule metric: drivedesk_workflow_rules
- public workflow rule outbox adapter key: internal.workflow
- public workflow task action surface
- public workflow adapter sync action surface
- public workflow action run history surface
- public workflow action run metric: drivedesk_workflow_action_runs
- public outbox recovery endpoint: /tenants/{tenant_id}/outbox-events/{event_id}/retry
- public outbox recovery audit event: outbox_event.retry_requested
- public integration connection endpoint: /tenants/{tenant_id}/integration-connections
- public integration mapping preview endpoint: /tenants/{tenant_id}/integration-mapping-preview
- public integration connection scope: file_import:execute
- public integration connection scope: file_import:preview
- public integration connection audit event: integration_connection.created
- public integration connection metric: drivedesk_integration_connections
- public tenant-owned repository helper surface
- public auth observability alerting surface
- public demo local run script
- public demo API contract smoke script
- public demo SDK smoke script
- curl, Python, and JavaScript public demo client examples
- public engineering surface docs
- public-only README
- public-only .nojekyll for GitHub Pages
- public-only .gitignore
- public-only CI workflow
- public-only smoke and secret-scan scripts

Not copied:

- private legacy runtime
- private operations docs
- backup and restore evidence
- infrastructure records from real servers
- payment/acquiring docs
- operations scripts
- private repository history
