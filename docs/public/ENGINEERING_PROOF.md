# Engineering Proof Contract

This document defines the public-safe proof surface exposed by the DriveDesk
Core demo. It is backed by the same synthetic payload in the static GitHub Pages
demo and in the read-only FastAPI endpoint:

```text
GET /demo/public
```

## Payload

The proof contract lives in:

```text
engineeringProof
```

It is linked from the public end-to-end scenario:

```text
approval -> notification -> adapter -> incident -> recovery -> proof
```

Required fields:

| Field | Contract |
| --- | --- |
| `milestone` | `engineering_70` |
| `status` | `validated` |
| `summary` | Four public-safe engineering state cards |
| `gates` | Executable validation commands |
| `evidence` | Public-safe docs and generated artifacts |

The connected scenario lives in `endToEndScenario` and points its final proof
step at `docs/public/ENGINEERING_PROOF.md`.

## Gates

| Gate | Command | Evidence |
| --- | --- | --- |
| Core smoke | `bash scripts/ci_smoke_public.sh` | API, worker, RBAC, outbox, integration, and observability checks |
| Public demo API | `bash scripts/check_public_demo_api.sh` | `GET /demo/public`, OpenAPI, examples, generated clients |
| Backup and restore | `bash scripts/check_public_backup_restore.sh` | `backup_sha256_recorded`, `restore_integrity_ok`, `counts_match` |
| Release safety | `bash scripts/check_public_release_rollback.sh && bash scripts/check_public_staged_promotion.sh` | rollback, canary gate, approval, promotion history |
| GitOps and IaC | `bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh` | Helm, Argo CD layout, OpenTofu plan, drift records |

## Evidence Chain

| Artifact | Purpose |
| --- | --- |
| `docs/public/SYSTEM_REVIEW_PATH.md` | Compact system route through public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index |
| `docs/public/REVIEWER_QUICKSTART.md` | Short 5-minute, 15-minute, and 45-minute external review path |
| `docs/public/PLATFORM_MATURITY_70.md` | Milestone contract and evidence groups |
| `docs/public/SANITIZED_EVIDENCE.md` | Sanitized runtime, recovery, release, GitOps, and boundary evidence |
| `docs/public/EVIDENCE_INDEX.md` | Public capability-to-evidence index contract |
| `docs/public/evidence/public-evidence-index.sanitized.json` | Machine-readable index of docs, evidence, verifiers, URLs, and boundaries |
| `docs/public/SYSTEM_DESIGN.md` | Core architecture, async boundaries, adapters, and observability |
| `endToEndScenario` in `GET /demo/public` | Reviewable workflow-to-proof path across notification, adapter, incident, and recovery layers |
| `sdk/generated/public-demo/` | OpenAPI-driven Python, JavaScript, and TypeScript clients with adapter operation plan helpers |

## Verification

Run the proof contract check:

```bash
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_evidence_index.sh
```

The check validates:

- the static demo payload;
- the FastAPI synthetic demo payload;
- the public demo HTML and JavaScript render surface;
- the generated OpenAPI schema;
- generated Python, JavaScript, and TypeScript SDK artifacts, including adapter operation plan helpers;
- the end-to-end scenario that links workflow, notification, adapter, incident,
  recovery, and proof evidence;
- referenced public-safe documents and evidence paths;
- public CI/export integration.

The same check is part of the public smoke path:

```bash
bash scripts/ci_smoke_public.sh
```
