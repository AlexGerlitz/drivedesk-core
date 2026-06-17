from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AdapterResult:
    adapter_key: str
    status: str
    message: str
    records_received: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    external_ref: str | None = None
    details: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


class AdapterExecutionError(Exception):
    def __init__(self, message: str, *, adapter_key: str, retryable: bool) -> None:
        super().__init__(message)
        self.message = message
        self.adapter_key = adapter_key
        self.retryable = retryable


class IntegrationAdapter(Protocol):
    adapter_key: str

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        ...


class NoopAdapter:
    adapter_key = "internal.noop"

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.adapter_key,
            status="success",
            message="Internal event acknowledged.",
            details={"event_passthrough": True, "payload_keys": sorted(payload.keys())},
        )


class FakeFileImportAdapter:
    adapter_key = "file.import.fake"

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        simulated_failure = payload.get("simulate_failure")
        if simulated_failure == "retryable":
            raise AdapterExecutionError(
                "Fake provider is temporarily unavailable.",
                adapter_key=self.adapter_key,
                retryable=True,
            )
        if simulated_failure == "permanent":
            raise AdapterExecutionError(
                "Fake provider rejected the import contract.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        records = payload.get("records")
        if not isinstance(records, list):
            raise AdapterExecutionError(
                "Import payload must contain a records list.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        accepted_external_ids: list[str] = []
        rejected = 0
        for record in records:
            if not isinstance(record, dict):
                rejected += 1
                continue
            external_id = str(record.get("external_id") or "").strip()
            display_name = str(record.get("display_name") or "").strip()
            if external_id and display_name:
                accepted_external_ids.append(external_id)
            else:
                rejected += 1

        accepted = len(accepted_external_ids)
        status = "success" if rejected == 0 else "partial_success"
        source_name = str(payload.get("source_name") or "fake-file")
        return AdapterResult(
            adapter_key=self.adapter_key,
            status=status,
            message=f"Imported {accepted} fake records from {source_name}.",
            records_received=len(records),
            records_accepted=accepted,
            records_rejected=rejected,
            external_ref=f"fake-import:{source_name}",
            details={
                "source_name": source_name,
                "source_format": str(payload.get("source_format") or "json"),
                "accepted_external_ids": accepted_external_ids,
            },
        )


ADAPTERS: dict[str, IntegrationAdapter] = {
    NoopAdapter.adapter_key: NoopAdapter(),
    FakeFileImportAdapter.adapter_key: FakeFileImportAdapter(),
}


def resolve_adapter(adapter_key: str | None) -> IntegrationAdapter:
    resolved_key = adapter_key or NoopAdapter.adapter_key
    adapter = ADAPTERS.get(resolved_key)
    if adapter is None:
        raise AdapterExecutionError(
            f"Unknown adapter: {resolved_key}",
            adapter_key=resolved_key,
            retryable=False,
        )
    return adapter


def execute_adapter(adapter_key: str | None, payload: dict[str, object]) -> AdapterResult:
    adapter = resolve_adapter(adapter_key)
    return adapter.execute(payload)
