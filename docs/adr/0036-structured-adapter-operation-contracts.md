# ADR-0036: Structured Adapter Operation Contracts

Status: accepted

## Context

DriveDesk adapters already expose runtime descriptors, connection mapping, and
connection scopes. The next Integration Hub step is making adapter operations
machine-readable.

Without structured operation contracts, UI screens, SDK examples, worker
behavior, and public docs would each need to infer operation behavior from prose
or hardcoded endpoint names.

## Decision

Adapter descriptors now include `operation_contracts`.

Each operation contract declares:

- operation key;
- human title;
- trigger;
- outbox event type or request event type;
- API or worker endpoint;
- required connection scope;
- idempotency keys;
- whether retry, dead-letter, and operator review apply.

The synthetic file-import adapter exposes two operations:

- `file_import_preview`, requiring `file_import:preview`;
- `file_import_execute`, requiring `file_import:execute`.

## Consequences

- Adapter behavior is discoverable through `GET /integration-adapters`.
- Public demo screens can show operation boundaries without exposing private
  provider values.
- Future adapters can document webhook, accounting, payment, and KKT operations
  through the same shape.
- UI and SDK generation can rely on contract metadata instead of hardcoded
  adapter assumptions.
