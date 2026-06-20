# Provider Sandbox Dry-Run

DriveDesk uses provider sandbox dry-run as the step between public-safe
connector onboarding and a real private connector rollout.

The current contract targets the Bitrix-style CRM adapter:

```text
adapter=crm.bitrix24.mock
operation=crm.deal.list
mode=read_only
```

It does not store or print real provider credentials. It checks that the
private runtime has the required secret reference names and can prepare a
bounded read-only provider request plan.

The same contract also includes a private runner shape:

```text
execute_provider_sandbox_dry_run
  -> build read-only request
  -> call injected private transport only when enabled
  -> normalize provider response
  -> return sanitized counts and redaction evidence
```

Public CI uses a fake transport. Real Bitrix24 access belongs only in the
private runtime with server-side secrets.

The operator CLI wraps the same core contract:

```bash
python scripts/run_provider_sandbox_dry_run.py --plan-only
python scripts/run_provider_sandbox_dry_run.py --execute-read-only --transport http
```

`--plan-only` checks that the private runtime has the required secret/config
references without touching the provider. `--execute-read-only --transport http`
performs one bounded read-only request and prints sanitized evidence only.
Public validation uses `--transport fake` so CI can prove the CLI behavior
without contacting a real provider.

## Why It Exists

Provider onboarding proves the adapter shape with synthetic data.

Provider sandbox dry-run proves the private runtime can safely approach a real
provider:

- required secret references are bound;
- tenant/provider config references are bound;
- the request is read-only;
- page size and timeout are bounded;
- provider calls are disabled by default;
- runner calls require explicit opt-in and injected private transport;
- operator CLI has plan-only and explicit read-only execution modes;
- runner output contains counts, buckets, dropped-key evidence, and
  reconciliation markers only;
- write mode remains locked;
- secret values, raw payloads, and provider tokens are not returned.

This is the bridge from portfolio-safe evidence to real commercial
integration work.

## Secret Boundary

The dry-run plan may mention reference names:

```text
BITRIX24_WEBHOOK_URL
BITRIX24_CLIENT_SECRET
BITRIX24_TENANT_DOMAIN
```

It must not include their values.

The browser, public export, generated SDK, GitHub Pages, and public evidence
must never contain provider tokens, webhook URLs, tenant domains, raw provider
payloads, or personal data.

## States

```text
blocked_missing_secret_binding
```

The private runtime is not ready to call the provider because one or more
required references are missing.

```text
ready_for_private_read_only_dry_run
```

All required references are present, but provider calls are still disabled.
This is the safe default for CI and public checks.

```text
provider_call_prepared
```

The request plan is prepared with provider-call intent enabled. It is still
read-only and has `externalMutation=false`. Real execution belongs only in the
private connector runtime.

## Verification

```bash
bash scripts/check_public_provider_sandbox_dry_run.sh
```

The check validates:

- missing env blocks the dry-run;
- fake secret values do not appear in JSON output;
- provider call is disabled by default;
- the fake transport is not called unless provider-call intent is enabled;
- the operator CLI reaches ready state in plan-only mode without leaking refs;
- the operator CLI completes fake read-only execution without leaking raw values;
- read-only operation is `crm.deal.list`;
- runner output excludes endpoint values, tokens, raw provider payloads,
  provider IDs, phone numbers, names, and email addresses;
- retryable transport failures redact exception messages;
- write mode stays locked;
- the request plan stays bounded.

Related checks:

```bash
bash scripts/check_public_provider_onboarding.sh
bash scripts/check_public_connector_fixture_replay.sh
bash scripts/public_repo_release_gate.sh
```

## What This Gives The Project

On an interview, this is the answer to:

> How would you connect a real CRM without leaking tokens or breaking customer
> data?

Short answer:

> I first certify the adapter contract with synthetic fixtures, then run a
> private read-only sandbox dry-run that checks secret binding, request shape,
> rate limits, redaction, and reconciliation before any write-mode provider
> operation is allowed.

That shows integration discipline, not just an API call.

For a real Bitrix24 sandbox, the only missing private step is binding real
server-side secret values and running the HTTP operator mode from the private
runtime. The public repository still proves the behavior without containing the
secrets.
