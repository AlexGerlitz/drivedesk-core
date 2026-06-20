# Review Console

The Review Console is the public-safe readiness console inside the DriveDesk
Core demo. It turns the project state into one browser-visible contract:

```text
readiness -> gates -> evidence -> handoff -> remaining work -> boundary
```

The contract is exposed in:

```text
GET /demo/public
reviewConsole
apps/admin/public-demo/
```

## Payload Contract

| Field | Purpose |
| --- | --- |
| `status` | Current review state for the public stand. |
| `updatedAt` | Public-safe timestamp for the review console snapshot. |
| `summary` | Four cards for public stand, DevOps proof, integration hub, and commercial rollout. |
| `gates` | Executable checks that prove the public stand. |
| `evidence` | Public-safe documents and machine-readable evidence. |
| `handoff` | What can be reviewed now and what moves to the next private step. |
| `remainingWork` | Product and commercial rollout gaps that are intentionally not claimed as done. |
| `boundary` | Public/private data and provider-mutation boundaries. |

## Gates

| Gate | Command | What it proves |
| --- | --- | --- |
| Public review bundle | `bash scripts/run_public_review_bundle.sh` | One-command route through entrypoint, docs, demo health, OpenAPI, SDK, evidence, and proof. |
| Review console contract | `bash scripts/check_public_review_console.sh` | Static demo, API payload, OpenAPI field, docs, evidence, and export wiring match. |
| Public export boundary | `bash scripts/public_repo_release_gate.sh` | Public repository receives only synthetic data, sanitized evidence, and public-safe scripts. |
| Provider sandbox dry-run | `bash scripts/check_public_provider_sandbox_dry_run.sh` | Fake transport, read-only runner, evidence recorder, and private-provider boundary. |

## Public Demo Surface

The public demo has a dedicated `Review` tab. It renders:

- readiness summary cards;
- review gates and commands;
- evidence artifacts;
- handoff items;
- remaining commercial rollout work;
- public/private boundary checks.

This tab is not a replacement for the full documentation. It is the fastest
browser-visible route for checking whether the public repository, demo payload,
API contract, evidence index, and release gates still describe the same system.

## Boundary

The Review Console uses synthetic data and sanitized evidence only. It does not
include production data, private runtime addresses, operational credentials, raw
logs, provider secrets, request bodies, or customer records.

Provider-changing work remains dry-run, approval-gated, and private-provider
only until a real rollout is approved.

## Verification

```bash
bash scripts/check_public_review_console.sh
bash scripts/run_public_review_bundle.sh
```

The check validates:

- `reviewConsole` in the static demo payload;
- `reviewConsole` in the FastAPI public demo payload;
- `reviewConsole` in the OpenAPI `PublicDemoRead` required fields;
- `Review` tab HTML and renderer wiring;
- public docs and evidence references;
- export script, private smoke path, public smoke path, and release gate wiring;
- public/private boundary markers.
