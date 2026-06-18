# DriveDesk Public Demo Shell

This is a static, read-only demo shell for the public DriveDesk Core repository.
It uses synthetic data and can be opened directly in a browser:

```text
apps/admin/public-demo/index.html
```

It can also load the synthetic FastAPI demo contract when a local API URL is
provided:

```text
apps/admin/public-demo/index.html?demoApi=http://localhost:8080/demo/public
```

Start that local API from the repository root:

```bash
bash scripts/run_public_demo_local.sh
```

Validate the API contract and example clients:

```bash
bash scripts/check_public_demo_api.sh
```

The shell is intentionally small. It gives the public repo a visible product
surface for the Core concepts that already exist in the backend:

- tenant;
- users and roles;
- audit events;
- outbox events;
- integration adapters;
- retry and dead-letter sync jobs;
- integration health metrics;
- alert routing, escalation, and runbook bindings;
- incident queue, recovery actions, and resolution evidence;
- synthetic workflow stages, timeline, and domain events;
- engineering proof gates and public-safe evidence chain;
- API-backed synthetic demo contract;
- API readiness;
- fake operational workflow state.
