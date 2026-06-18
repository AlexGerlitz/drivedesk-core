from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class LifecycleTransition:
    from_status: str
    to_statuses: list[str]
    reason: str


@dataclass(frozen=True)
class LifecyclePolicy:
    record_type: str
    initial_status: str
    statuses: list[str]
    terminal_statuses: list[str]
    transitions: list[LifecycleTransition] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return asdict(self)

    def allowed_next_statuses(self, current_status: str) -> list[str]:
        for transition in self.transitions:
            if transition.from_status == current_status:
                return list(transition.to_statuses)
        return []


LIFECYCLE_POLICIES: dict[str, LifecyclePolicy] = {
    "contract": LifecyclePolicy(
        record_type="contract",
        initial_status="draft",
        statuses=["draft", "approved", "pending_signature", "active", "completed", "cancelled"],
        terminal_statuses=["completed", "cancelled"],
        transitions=[
            LifecycleTransition(
                from_status="draft",
                to_statuses=["approved", "pending_signature", "cancelled"],
                reason="Contract can be approved, sent for signature, or cancelled before activation.",
            ),
            LifecycleTransition(
                from_status="approved",
                to_statuses=["active", "cancelled"],
                reason="Approved contracts can become active or be cancelled before training starts.",
            ),
            LifecycleTransition(
                from_status="pending_signature",
                to_statuses=["active", "cancelled"],
                reason="Contracts waiting for signature can become active or be cancelled.",
            ),
            LifecycleTransition(
                from_status="active",
                to_statuses=["completed", "cancelled"],
                reason="Active contracts finish successfully or are cancelled.",
            ),
        ],
    ),
    "payment": LifecyclePolicy(
        record_type="payment",
        initial_status="pending",
        statuses=["pending", "confirmed", "failed", "cancelled", "refunded"],
        terminal_statuses=["cancelled", "refunded"],
        transitions=[
            LifecycleTransition(
                from_status="pending",
                to_statuses=["confirmed", "failed", "cancelled"],
                reason="Pending payments can be confirmed, fail, or be cancelled.",
            ),
            LifecycleTransition(
                from_status="confirmed",
                to_statuses=["refunded"],
                reason="Confirmed payments can be refunded through a controlled flow.",
            ),
            LifecycleTransition(
                from_status="failed",
                to_statuses=["pending", "cancelled"],
                reason="Failed payments can be retried or cancelled.",
            ),
        ],
    ),
    "lesson": LifecyclePolicy(
        record_type="lesson",
        initial_status="scheduled",
        statuses=["scheduled", "rescheduled", "completed", "cancelled"],
        terminal_statuses=["completed", "cancelled"],
        transitions=[
            LifecycleTransition(
                from_status="scheduled",
                to_statuses=["completed", "rescheduled", "cancelled"],
                reason="Scheduled lessons can be completed, moved, or cancelled.",
            ),
            LifecycleTransition(
                from_status="rescheduled",
                to_statuses=["scheduled", "cancelled"],
                reason="Rescheduled lessons return to the schedule or are cancelled.",
            ),
        ],
    ),
    "task": LifecyclePolicy(
        record_type="task",
        initial_status="open",
        statuses=["open", "in_progress", "blocked", "done", "cancelled"],
        terminal_statuses=["done", "cancelled"],
        transitions=[
            LifecycleTransition(
                from_status="open",
                to_statuses=["in_progress", "done", "cancelled"],
                reason="Open tasks can start, be completed immediately, or be cancelled.",
            ),
            LifecycleTransition(
                from_status="in_progress",
                to_statuses=["blocked", "done", "cancelled"],
                reason="Tasks in progress can be blocked, completed, or cancelled.",
            ),
            LifecycleTransition(
                from_status="blocked",
                to_statuses=["in_progress", "cancelled"],
                reason="Blocked tasks can resume or be cancelled.",
            ),
        ],
    ),
    "document": LifecyclePolicy(
        record_type="document",
        initial_status="draft",
        statuses=["draft", "generated", "signed", "archived", "cancelled"],
        terminal_statuses=["archived", "cancelled"],
        transitions=[
            LifecycleTransition(
                from_status="draft",
                to_statuses=["generated", "cancelled"],
                reason="Draft documents can be generated or cancelled.",
            ),
            LifecycleTransition(
                from_status="generated",
                to_statuses=["signed", "archived", "cancelled"],
                reason="Generated documents can be signed, archived, or cancelled.",
            ),
            LifecycleTransition(
                from_status="signed",
                to_statuses=["archived"],
                reason="Signed documents can be archived.",
            ),
        ],
    ),
}


def list_lifecycle_policies() -> list[dict[str, object]]:
    return [LIFECYCLE_POLICIES[key].to_payload() for key in sorted(LIFECYCLE_POLICIES)]


def describe_lifecycle_policy(record_type: str) -> LifecyclePolicy:
    if record_type not in LIFECYCLE_POLICIES:
        raise KeyError(record_type)
    return LIFECYCLE_POLICIES[record_type]


def preview_lifecycle_transition(record_type: str, from_status: str, to_status: str) -> dict[str, object]:
    policy = describe_lifecycle_policy(record_type)
    allowed_next_statuses = policy.allowed_next_statuses(from_status)
    valid = to_status in allowed_next_statuses
    if valid:
        reason = f"{record_type} can move from {from_status} to {to_status}."
    elif from_status in policy.terminal_statuses:
        reason = f"{from_status} is terminal for {record_type}."
    elif from_status not in policy.statuses:
        reason = f"{from_status} is not a known status for {record_type}."
    elif to_status not in policy.statuses:
        reason = f"{to_status} is not a known status for {record_type}."
    else:
        reason = f"{record_type} cannot move from {from_status} to {to_status}."

    return {
        "record_type": record_type,
        "from_status": from_status,
        "to_status": to_status,
        "valid": valid,
        "reason": reason,
        "allowed_next_statuses": allowed_next_statuses,
        "terminal": from_status in policy.terminal_statuses,
    }
