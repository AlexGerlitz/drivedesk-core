# DevOps Roadmap

DriveDesk should become the project where infrastructure work is practiced on a
real backend instead of abstract examples.

## Foundation Layer

Implemented baseline:

- Python import/compile smoke checks;
- pytest;
- custom secret scan script;
- Docker Compose validation when Docker is available;
- legacy image build in CI;
- DriveDesk foundation image build in CI;
- DriveDesk Core API, RBAC, audit, and outbox tests;
- manual and scheduled security audit workflow already present in the repo.
- public-safe synthetic backup/restore drill for the exported Core surface.

What this gives us:

- broken imports are caught early;
- tests run on every push;
- obvious committed secrets are caught before merge;
- Docker image problems show up before deployment;
- the new foundation is checked alongside the old runtime.
- tenant, user, audit, and outbox behavior is covered before deployment work
  starts.
- backup/restore can be demonstrated without copying private data into the
  public repository.

## Next Layers

Recommended next DevOps tasks:

1. Add more deployment evidence around release rollback and SLO burn.
2. Broaden generated client examples from the OpenAPI schema.
3. Add a Helm chart skeleton after the compose contract is stable.
4. Add Terraform/OpenTofu only after the target infrastructure shape is clear.

## Human Summary

The point is not to collect tools. The point is to make every tool answer a
real operational question: can it build, can it run, can it be restored, can it
be observed, and can it be changed without chaos.
