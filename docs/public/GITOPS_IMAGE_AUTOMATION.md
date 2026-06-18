# GitOps Image Automation Evidence

DriveDesk includes a public-safe image automation drill for the GitOps delivery
model. It shows how a CI-built image becomes a GitOps update proposal.

## Command

```bash
bash scripts/check_public_gitops_image_automation.sh
```

## What The Check Does

The check validates the synthetic image automation flow:

```text
CI build
    |
image tag + digest
    |
SBOM + scan + provenance
    |
GitOps update proposal
    |
pull-request-only review path
```

The check verifies:

- candidate image tag is recorded;
- image digest is recorded;
- SBOM, scan, and provenance evidence are attached;
- critical and high vulnerability counts are zero in the synthetic evidence;
- target GitOps files are recorded;
- evidence gates are referenced;
- the update is pull-request-only;
- no registry or cluster mutation is performed;
- `gitops.image_update.proposed` evidence is recorded;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_gitops_image_automation",
  "data_profile": "synthetic_fake_data",
  "automation_model": "ci_image_build_to_gitops_update_proposal",
  "checks": {
    "image_digest_recorded": true,
    "sbom_attached": true,
    "pull_request_only_no_mutation": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drill uses a synthetic image digest and synthetic supply-chain
metadata. It does not include live registry credentials, private runner labels,
server-specific addresses, raw logs, runtime connection values, production
data, or incident payloads.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/gitops-image-automation.sanitized.json
```

## Why This Matters

GitOps becomes stronger when image updates are not edited by hand. This drill
shows the expected automation boundary: CI produces a candidate image record,
security evidence is attached, GitOps manifests receive a proposed update, and
humans still review the change before promotion.
