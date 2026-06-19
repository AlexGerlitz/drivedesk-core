from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntegrationRunbook:
    key: str
    title: str
    severity: str
    source_type: str
    source_statuses: tuple[str, ...]
    alert_name: str | None
    summary: str
    recommended_actions: tuple[str, ...]
    evidence_fields: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "severity": self.severity,
            "source_type": self.source_type,
            "source_statuses": list(self.source_statuses),
            "alert_name": self.alert_name,
            "summary": self.summary,
            "recommended_actions": list(self.recommended_actions),
            "evidence_fields": list(self.evidence_fields),
        }


INTEGRATION_RUNBOOKS: tuple[IntegrationRunbook, ...] = (
    IntegrationRunbook(
        key="integration.retry_backlog",
        title="Retryable integration backlog",
        severity="warning",
        source_type="outbox_event",
        source_statuses=("retry",),
        alert_name="DriveDeskIntegrationRetries",
        summary="Retryable adapter jobs are waiting for provider recovery or operator confirmation.",
        recommended_actions=(
            "Check connection diagnostics for the affected adapter.",
            "Review retryable operator-review items and provider status.",
            "Wait for provider recovery or retry after confirming the failure cleared.",
        ),
        evidence_fields=("adapter_key", "operation_key", "attempts", "last_error", "payload_summary"),
    ),
    IntegrationRunbook(
        key="integration.dead_letter",
        title="Dead-lettered integration job",
        severity="critical",
        source_type="outbox_event",
        source_statuses=("dead_letter",),
        alert_name="DriveDeskIntegrationDeadLetters",
        summary="An adapter job exhausted retry policy or hit a permanent provider contract error.",
        recommended_actions=(
            "Inspect the safe payload summary and required operation scope.",
            "Fix mapping, connection scope, provider contract, or input data.",
            "Requeue the outbox event with an audited operator reason after the fix.",
        ),
        evidence_fields=("adapter_key", "operation_key", "attempts", "last_error", "payload_summary"),
    ),
    IntegrationRunbook(
        key="integration.reconciliation_mismatch",
        title="Provider evidence mismatch",
        severity="critical",
        source_type="reconciliation",
        source_statuses=("mismatched",),
        alert_name="DriveDeskIntegrationReconciliationMismatch",
        summary="Provider-side evidence does not match the result recorded by DriveDesk.",
        recommended_actions=(
            "Review reconciliation diff keys and provider status.",
            "Verify provider dashboard, batch status, and adapter mapping.",
            "Create a corrective task before marking the incident resolved.",
        ),
        evidence_fields=("adapter_key", "operation_key", "diff_keys", "provider_status"),
    ),
    IntegrationRunbook(
        key="integration.reconciliation_blocked",
        title="Blocked provider reconciliation",
        severity="critical",
        source_type="reconciliation",
        source_statuses=("blocked",),
        alert_name="DriveDeskIntegrationReconciliationBlocked",
        summary="Reconciliation is blocked because the related adapter job is dead-lettered.",
        recommended_actions=(
            "Handle the dead-lettered outbox event first.",
            "Use operator review to fix the adapter job and retry it.",
            "Record reconciliation again after the job has processed evidence.",
        ),
        evidence_fields=("adapter_key", "operation_key", "outbox_event_id", "diff_keys"),
    ),
    IntegrationRunbook(
        key="integration.reconciliation_pending",
        title="Pending provider reconciliation",
        severity="info",
        source_type="reconciliation",
        source_statuses=("pending",),
        alert_name=None,
        summary="Reconciliation was recorded before the outbox job produced final evidence.",
        recommended_actions=(
            "Wait for worker execution or check the outbox backlog.",
            "Re-run reconciliation when the provider has final evidence.",
        ),
        evidence_fields=("adapter_key", "operation_key", "outbox_event_id"),
    ),
)


def list_integration_runbooks() -> list[dict[str, object]]:
    return [runbook.to_payload() for runbook in INTEGRATION_RUNBOOKS]


def select_integration_runbook(source_type: str, source_status: str) -> dict[str, object] | None:
    for runbook in INTEGRATION_RUNBOOKS:
        if runbook.source_type == source_type and source_status in runbook.source_statuses:
            return runbook.to_payload()
    return None


def _required_runbook(source_type: str, source_status: str) -> dict[str, object]:
    runbook = select_integration_runbook(source_type, source_status)
    if runbook is None:
        raise ValueError(f"No integration runbook for {source_type}:{source_status}")
    return runbook


def build_integration_repair_workbench() -> dict[str, object]:
    """Build a public-safe repair matrix for failed integration work.

    The workbench is intentionally synthetic: it proves how DriveDesk classifies
    integration failures, routes them to runbooks, and proposes safe repair
    actions without executing provider calls or exposing raw payloads.
    """

    incidents = [
        {
            "incident_id": "IR-001",
            "source_type": "outbox_event",
            "source_status": "retry",
            "adapter_key": "accounting.export.mock",
            "operation_key": "accounting_export_execute",
            "status": "retryable",
            "severity": "warning",
            "business_impact": "Accounting export is delayed but the workflow remains recoverable.",
            "safe_payload_summary": {
                "records": 2,
                "amount_bucket": "2001-5000",
                "payload_hash_recorded": True,
            },
            "attempts": 2,
            "next_action": "run_connection_diagnostics",
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "integration_repair.retry_backlog_classified",
        },
        {
            "incident_id": "IR-002",
            "source_type": "outbox_event",
            "source_status": "dead_letter",
            "adapter_key": "crm.bitrix24.mock",
            "operation_key": "crm_deal_ingest_execute",
            "status": "operator_review",
            "severity": "critical",
            "business_impact": "CRM deal facts are blocked until mapping or scope is corrected.",
            "safe_payload_summary": {
                "records": 1,
                "missing_mapping": ["deal_id"],
                "payload_hash_recorded": True,
            },
            "attempts": 3,
            "next_action": "fix_mapping_profile",
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "integration_repair.dead_letter_classified",
        },
        {
            "incident_id": "IR-003",
            "source_type": "reconciliation",
            "source_status": "mismatched",
            "adapter_key": "accounting.export.mock",
            "operation_key": "accounting_export_execute",
            "status": "needs_review",
            "severity": "critical",
            "business_impact": "Provider evidence does not match DriveDesk expected result.",
            "safe_payload_summary": {
                "diff_keys": ["records_accepted", "provider_status"],
                "provider_status": "partial_success",
            },
            "attempts": 1,
            "next_action": "open_reconciliation_review",
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "integration_repair.reconciliation_mismatch_classified",
        },
    ]

    runbook_rows: list[dict[str, object]] = []
    for incident in incidents:
        runbook = _required_runbook(
            str(incident["source_type"]),
            str(incident["source_status"]),
        )
        runbook_rows.append(
            {
                "incident_id": incident["incident_id"],
                "runbook_key": runbook["key"],
                "title": runbook["title"],
                "severity": runbook["severity"],
                "alert_name": runbook["alert_name"],
                "recommended_actions": runbook["recommended_actions"],
                "evidence_fields": runbook["evidence_fields"],
                "evidence": "integration_repair.runbook_attached",
            }
        )

    impact_analysis = [
        {
            "area": "workflow_delivery",
            "status": "degraded",
            "affected_items": 2,
            "detail": "Two downstream workflow steps wait for adapter recovery evidence.",
            "external_mutation": False,
            "evidence": "integration_repair.impact.workflow_delivery",
        },
        {
            "area": "financial_reconciliation",
            "status": "at_risk",
            "affected_items": 1,
            "detail": "One export needs reconciliation review before finance closure.",
            "external_mutation": False,
            "evidence": "integration_repair.impact.financial_reconciliation",
        },
        {
            "area": "operator_queue",
            "status": "actionable",
            "affected_items": 3,
            "detail": "All incidents have a runbook, owner path, and safe next action.",
            "external_mutation": False,
            "evidence": "integration_repair.impact.operator_queue",
        },
    ]

    repair_actions = [
        {
            "action": "run_connection_diagnostics",
            "target": "accounting.export.mock",
            "status": "safe_dry_run",
            "source_incident": "IR-001",
            "requires_approval": False,
            "safe_to_auto_run": True,
            "external_mutation": False,
            "provider_call_enabled": False,
            "rollback": "no_state_change",
            "evidence": "integration_repair.action.diagnostics",
        },
        {
            "action": "retry_after_diagnostics",
            "target": "accounting.export.mock",
            "status": "approval_required",
            "source_incident": "IR-001",
            "requires_approval": True,
            "safe_to_auto_run": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "rollback": "keep_previous_outbox_attempt",
            "evidence": "integration_repair.action.retry",
        },
        {
            "action": "fix_mapping_profile",
            "target": "crm.bitrix24.mock",
            "status": "operator_review",
            "source_incident": "IR-002",
            "requires_approval": True,
            "safe_to_auto_run": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "rollback": "restore_previous_mapping_profile",
            "evidence": "integration_repair.action.mapping_fix",
        },
        {
            "action": "open_reconciliation_review",
            "target": "accounting.export.mock",
            "status": "operator_review",
            "source_incident": "IR-003",
            "requires_approval": False,
            "safe_to_auto_run": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "rollback": "review_only",
            "evidence": "integration_repair.action.reconciliation_review",
        },
    ]

    safe_execution_plan = [
        {
            "step": "classify_failure",
            "status": "ready",
            "detail": "Source status selects retry, dead-letter, or reconciliation runbook.",
            "external_mutation": False,
            "evidence": "integration_repair.failure_classified",
        },
        {
            "step": "attach_business_impact",
            "status": "ready",
            "detail": "Operator sees workflow, finance, and queue impact before touching the job.",
            "external_mutation": False,
            "evidence": "integration_repair.impact_attached",
        },
        {
            "step": "prepare_safe_actions",
            "status": "ready",
            "detail": "Diagnostics, mapping fix, retry, and reconciliation review are separated.",
            "external_mutation": False,
            "evidence": "integration_repair.actions_prepared",
        },
        {
            "step": "dry_run_first",
            "status": "enforced",
            "detail": "Public contract exposes only dry-run and review actions.",
            "external_mutation": False,
            "evidence": "integration_repair.dry_run_enforced",
        },
        {
            "step": "approval_before_commit",
            "status": "locked",
            "detail": "Retry or provider-changing repair requires approval and idempotency evidence.",
            "external_mutation": False,
            "evidence": "integration_repair.approval_required",
        },
        {
            "step": "observe_after_repair",
            "status": "planned",
            "detail": "Repair closure requires updated reconciliation, metrics, and incident evidence.",
            "external_mutation": False,
            "evidence": "integration_repair.postcheck_planned",
        },
    ]

    data_boundaries = [
        {
            "name": "repair_preview_only",
            "status": "clean",
            "contains_pii": False,
            "raw_payload_included": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "detail": "The workbench computes repair guidance from synthetic status and evidence references.",
        },
        {
            "name": "safe_payload_summary",
            "status": "clean",
            "contains_pii": False,
            "raw_payload_included": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "detail": "Operators see counts, buckets, diff keys, and hashes instead of raw provider payloads.",
        },
        {
            "name": "approval_before_retry",
            "status": "locked",
            "contains_pii": False,
            "raw_payload_included": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "detail": "State-changing repair remains locked behind approval, idempotency, and audit evidence.",
        },
        {
            "name": "private_provider_boundary",
            "status": "closed",
            "contains_pii": False,
            "raw_payload_included": False,
            "external_mutation": False,
            "provider_call_enabled": False,
            "detail": "Real provider calls belong only to the private connector runtime.",
        },
    ]

    return {
        "status": "previewed",
        "repair_level": "operator_repair_ready",
        "incident_count": len(incidents),
        "critical_count": sum(1 for item in incidents if item["severity"] == "critical"),
        "safe_action_count": sum(1 for item in repair_actions if item["safe_to_auto_run"]),
        "summary": [
            {
                "label": "Incidents",
                "value": str(len(incidents)),
                "detail": "retry, dead-letter, reconciliation",
                "tone": "amber",
            },
            {
                "label": "Critical",
                "value": "2",
                "detail": "operator review required",
                "tone": "red",
            },
            {
                "label": "Safe actions",
                "value": "1",
                "detail": "diagnostics can run first",
                "tone": "green",
            },
            {
                "label": "Provider writes",
                "value": "0",
                "detail": "blocked in public preview",
                "tone": "violet",
            },
        ],
        "incident_matrix": incidents,
        "repair_runbooks": runbook_rows,
        "impact_analysis": impact_analysis,
        "repair_actions": repair_actions,
        "safe_execution_plan": safe_execution_plan,
        "data_boundaries": data_boundaries,
        "api": {
            "standalone": "GET /demo/integration-repair",
            "operator_review": "GET /tenants/{tenant_id}/integration-operator-review",
            "retry": "POST /tenants/{tenant_id}/outbox-events/{event_id}/retry",
            "incidents": "GET /tenants/{tenant_id}/integration-incidents",
            "reconciliations": "GET /tenants/{tenant_id}/integration-reconciliations",
        },
        "docs": [
            {
                "label": "Integration repair",
                "path": "docs/public/INTEGRATION_REPAIR.md",
                "check": "bash scripts/check_public_integration_repair.sh",
            },
            {
                "label": "Incident runbooks",
                "path": "docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md",
                "check": "bash scripts/check_public_demo_api.sh",
            },
            {
                "label": "Integration execution",
                "path": "docs/public/INTEGRATION_EXECUTION.md",
                "check": "bash scripts/check_public_integration_execution.sh",
            },
            {
                "label": "Provider onboarding",
                "path": "docs/public/PROVIDER_ONBOARDING.md",
                "check": "bash scripts/check_public_provider_onboarding.sh",
            },
        ],
    }
