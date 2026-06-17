# ADR-0001: Modular Monolith First

Status: accepted

## Context

DriveDesk Core needs enough structure to support multiple product areas, but it
does not yet have a scaling reason to split into distributed services.

## Decision

Start as a modular monolith:

- shared database;
- clear package boundaries;
- API, worker, and core domain modules;
- outbox for future asynchronous integrations;
- migrations and tests from the beginning.

## Consequences

- Local development stays simple.
- CI remains fast.
- Modules can be extracted later if a real operational reason appears.
- Boundaries are documented without paying microservice complexity too early.
