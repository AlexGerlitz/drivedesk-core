# DriveDesk Public Engineering Surface

This folder contains the public-safe engineering surface for DriveDesk. It is
written so an external reviewer can understand the project without access to
private infrastructure, production history, customer data, or operational
credentials.

## Documents

- `PORTFOLIO_CASE_STUDY.md` - engineering case study and current system shape.
- `ARCHITECTURE_DIAGRAMS.md` - public-safe architecture diagrams.
- `PUBLIC_DEMO_PLAN.md` - future live demo plan.
- `SANITIZED_EVIDENCE.md` - human-readable staging evidence summary.
- `evidence/de-staging-evidence.sanitized.json` - machine-readable sanitized
  evidence snapshot.

The public repository export also generates:

- `docs/openapi.json` - FastAPI OpenAPI schema from the exported API.
- `PUBLIC_EXPORT_MANIFEST.md` - file list and export boundary summary.

## Human Explanation

The private repository keeps building the real product. This folder is the
clean explanation layer for hiring and public review: what was built, why it was
built that way, what checks exist, and how the architecture can evolve.

The export release gate makes this repeatable. Instead of manually copying
files, the private source builds a fresh public package, validates the schema,
runs public smoke checks, and leaves the result ready for a separate public
repository.
