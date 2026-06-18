# Sanitized Engineering Evidence

This document summarizes a private staging evidence run in a public-safe form.
It keeps the engineering facts while omitting private hostnames, addresses,
internal paths, credentials, and raw logs.

## Evidence Snapshot

Source file:

```text
docs/public/evidence/de-staging-evidence.sanitized.json
```

Recovery drill source file:

```text
docs/public/evidence/backup-restore-drill.sanitized.json
```

Release rollback drill source file:

```text
docs/public/evidence/release-rollback-drill.sanitized.json
```

Verified signals:

- CI completed successfully;
- staging deploy completed successfully;
- staging health workflow completed successfully;
- staging evidence workflow completed successfully;
- API listener was private;
- Prometheus listener was private;
- Grafana listener was private;
- Loki listener was private;
- Grafana Alloy listener was private;
- Alertmanager listener was private;
- Prometheus scraped required targets;
- Loki returned recent API logs;
- Alertmanager was ready;
- Prometheus loaded alert rules;
- active alerts count was zero at collection time.
- the public synthetic backup/restore drill created a temporary backup artifact;
- the restore target passed integrity checks;
- restored row counts matched the source counts;
- production data was not touched.
- the public synthetic release rollback drill promoted a candidate release;
- the candidate readiness failure was detected;
- rollback returned `current` to the stable release;
- `release.rollback.executed` evidence was recorded.

## Human Explanation

The evidence proves that the project is not just code in a repository. A real
staging runtime was deployed, checked, observed, and summarized by automation.
The public version keeps only the operational shape and health results.

## What This Shows

- CI/CD is wired end to end.
- Health and readiness checks exist.
- Metrics are collected.
- Logs are collected.
- Alert rules are loaded.
- Alertmanager is reachable.
- Evidence is machine-readable.
- Backup/restore is checked through an executable public drill.
- Bad-release rollback is checked through an executable public drill.

## What This Leaves Out

The public evidence omits raw logs, request bodies, private infrastructure
labels, credentials, internal hostnames, and server-specific addresses.
