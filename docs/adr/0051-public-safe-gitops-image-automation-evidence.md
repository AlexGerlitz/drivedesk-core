# ADR-0051: Public-Safe GitOps Image Automation Evidence

Status: accepted

## Context

DriveDesk has public-safe GitOps delivery, image promotion, drift detection,
and drift remediation evidence. The next operational question is:

```text
How does a newly built image tag enter the GitOps promotion flow?
```

The public repository must not contain registry credentials, private runner
labels, live cluster endpoints, runtime connection values, raw logs, or
production data.

## Decision

Add public-safe GitOps image automation evidence:

```text
infra/gitops/image-automation/build-artifact.yaml
infra/gitops/image-automation/update-proposal.yaml
```

Add an executable check:

```text
scripts/check_public_gitops_image_automation.sh
```

The check validates the synthetic CI image build record, image tag, digest,
SBOM, scan result, provenance, GitOps update proposal, evidence gates, and the
pull-request-only no-mutation boundary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/gitops-image-automation.sanitized.json
```

It records the image automation shape without registry credentials, private
runner labels, live endpoints, addresses, raw logs, runtime connection values,
or production data.

## Consequences

- The public project now demonstrates how image automation connects CI output
  to GitOps promotion.
- The evidence remains synthetic and readable.
- This is not a claim that a public image was pushed to a live registry.
