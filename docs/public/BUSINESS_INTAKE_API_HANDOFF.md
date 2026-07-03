# Business Intake API Handoff

This is the shortest recruiter-facing route through DriveDesk Core.

```text
Telegram-style intake
  -> FastAPI preview endpoint
  -> validated business record shape
  -> admin workbench queue
  -> status transition
  -> outbox/integration handoff
  -> pytest/API smoke/CI
```

It is intentionally narrower than the full platform tour. The goal is to show
one backend/API workflow that can be inspected in under one minute.

## 60-Second Review

| Step | Public artifact | What to check |
| --- | --- | --- |
| Intake contract | `GET /demo/business-intake-pipeline` | CRM, bank, and accounting facts are normalized into safe context. |
| API boundary | `POST /tenants/{tenant_id}/business-intake-pipeline/preview` | Preview endpoint returns the action plan without provider writes. |
| Admin queue | `apps/admin/public-demo/index.html` | The public demo renders workbench cards, action rows, and boundaries. |
| Task handoff | `GET /demo/business-task-handoff` | Action-plan steps become internal task cards and outbox candidates. |
| SDK/OpenAPI | `docs/openapi.json`, `sdk/generated/public-demo/` | The route is part of the generated API contract. |
| Tests | `tests/test_drivedesk_core_api.py`, `bash scripts/ci_smoke_public.sh` | The route is covered by API smoke, generated SDK smoke, and CI. |

## Why This Is the Best First-Job Proof

This slice maps directly to backend, API automation, QA/API, and integration
roles:

- validates incoming facts before they become operator work;
- keeps unsafe provider payloads out of the public response;
- exposes FastAPI routes and generated OpenAPI/SDK artifacts;
- shows tenant/API boundaries without claiming finished SaaS;
- connects admin UI, API, outbox/integration handoff, tests, and release gates.

## Public-Safe Demo Route

The live static demo uses only synthetic data:

```text
apps/admin/public-demo/
```

The screenshot used by the public review route is:

```text
docs/public/assets/drivedesk-core-demo-overview.png
```

Use these commands for verification:

```bash
bash scripts/check_public_business_intake_api_handoff.sh
bash scripts/check_public_business_intake_pipeline.sh
bash scripts/check_public_business_task_handoff.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
```

## Privacy Boundary

This route must stay boring and synthetic:

- no real names;
- no phone numbers;
- no Telegram or chat IDs;
- no admin URLs;
- no raw provider payloads;
- no request bodies from production;
- no logs, dumps, hostnames, tokens, or credentials;
- no external provider writes.

Related docs:

- `docs/public/BUSINESS_INTAKE_PIPELINE.md`
- `docs/public/BUSINESS_TASK_HANDOFF.md`
- `docs/public/API_BACKED_DEMO.md`
- `docs/public/CLIENT_SDK.md`
- `docs/public/SYSTEM_REVIEW_PATH.md`
