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
