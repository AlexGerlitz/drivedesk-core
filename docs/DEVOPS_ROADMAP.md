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
- public-safe synthetic release rollback drill for the exported Core surface.
- public-safe synthetic SLO canary gate drill for the exported Core surface.
- public-safe synthetic staged promotion drill for the exported Core surface.
- public-safe Helm chart foundation and render validation for the exported Core surface.
- public-safe OpenTofu plan evidence for the exported Core surface.
- public-safe GitOps delivery foundation and Argo CD layout validation for the exported Core surface.
- public-safe GitOps image promotion and drift detection for the exported Core surface.
- public-safe GitOps drift remediation planning for the exported Core surface.
- public-safe GitOps image automation evidence for the exported Core surface.

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
- bad-release rollback can be demonstrated without exposing private deployment
  targets.
- bad candidates can be blocked by SLO-style promotion gates without exposing
  private metrics or deployment targets.
- safe candidates can be promoted through auditable build, staging, canary, and
  production gates without exposing private deployment targets.
- the modular monolith now has a Kubernetes-style packaging path without
  pretending the app is already a microservice platform.
- OpenTofu plan evidence records infrastructure shape, environment model, state
  boundary, secret boundary, and zero-destroy plan-only behavior without
  touching a real cloud account.
- GitOps desired-state delivery connects the Helm chart to build, staging,
  canary, and production promotion flow without exposing a live cluster.
- image promotion and drift evidence shows the difference between desired state
  and observed state, including a safe rollback tag.
- drift remediation evidence shows the response path after detection:
  reconcile after approval, rollback if needed, or block unsafe changes.
- image automation evidence shows how a candidate image digest, SBOM, scanner
  result, provenance, and GitOps update proposal move toward review without
  mutating a registry or cluster directly.

## Next Layers

Recommended next DevOps tasks:

1. Broaden generated client examples from the OpenAPI schema.
2. Add private runtime rollout evidence for the staging control plane.
3. Add public-safe infrastructure state drift evidence.
4. Add policy-as-code proposals only as text-only design notes unless the owner
   explicitly requests policy changes.

## Human Summary

The point is not to collect tools. The point is to make every tool answer a
real operational question: can it build, can it run, can it be restored, can it
be observed, and can it be changed without chaos.
