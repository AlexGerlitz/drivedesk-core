from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import perf_counter

from drivedesk_api.observability import log_json
from drivedesk_api.services import list_processable_outbox, mark_outbox_failed, mark_outbox_processed
from drivedesk_api.session import SessionLocal
from drivedesk_api.settings import get_settings
from drivedesk_core import AdapterExecutionError, __version__ as core_version, execute_adapter


adapter_logger = logging.getLogger("drivedesk.worker.adapters")


@dataclass(frozen=True)
class WorkerHeartbeat:
    event_type: str
    service: str
    environment: str
    status: str
    core_version: str
    checked_at: str
    processed_outbox_events: int = 0


def build_heartbeat(processed_outbox_events: int = 0, environment: str | None = None) -> WorkerHeartbeat:
    settings = get_settings()
    return WorkerHeartbeat(
        event_type="worker.heartbeat",
        service="drivedesk-worker",
        environment=environment or settings.environment,
        status="ok",
        core_version=core_version,
        checked_at=datetime.now(UTC).isoformat(),
        processed_outbox_events=processed_outbox_events,
    )


def heartbeat_to_json(heartbeat: WorkerHeartbeat) -> str:
    return json.dumps(asdict(heartbeat), ensure_ascii=False, sort_keys=True)


async def run_once() -> dict[str, object]:
    processed = await process_outbox_once()
    return asdict(build_heartbeat(processed_outbox_events=processed))


async def process_outbox_once(limit: int = 25, session_factory=SessionLocal) -> int:
    async with session_factory() as session:
        events = await list_processable_outbox(session, limit=limit)
        processed = 0
        for event in events:
            adapter_key = event.adapter_key or "internal.noop"
            attempt = event.attempts + 1
            started_at = perf_counter()
            log_json(
                adapter_logger,
                "adapter.started",
                service="drivedesk-worker",
                adapter_key=adapter_key,
                outbox_event_id=event.id,
                tenant_id=event.tenant_id,
                outbox_event_type=event.event_type,
                attempt=attempt,
            )
            try:
                payload = json.loads(event.payload_json)
                if not isinstance(payload, dict):
                    raise AdapterExecutionError(
                        "Outbox payload must be a JSON object.",
                        adapter_key=adapter_key,
                        retryable=False,
                    )
                result = execute_adapter(adapter_key, payload)
                duration_ms = round((perf_counter() - started_at) * 1000, 3)
                await mark_outbox_processed(session, event, result=result.to_payload(), duration_ms=duration_ms)
                log_json(
                    adapter_logger,
                    "adapter.completed",
                    service="drivedesk-worker",
                    adapter_key=adapter_key,
                    outbox_event_id=event.id,
                    tenant_id=event.tenant_id,
                    outbox_event_type=event.event_type,
                    attempt=attempt,
                    duration_ms=duration_ms,
                    result_status=result.status,
                    records_received=result.records_received,
                    records_accepted=result.records_accepted,
                    records_rejected=result.records_rejected,
                )
            except AdapterExecutionError as exc:
                duration_ms = round((perf_counter() - started_at) * 1000, 3)
                await mark_outbox_failed(
                    session,
                    event,
                    error_message=exc.message,
                    retryable=exc.retryable,
                    duration_ms=duration_ms,
                )
                failed_event_type = "adapter.failed" if exc.retryable and event.status == "retry" else "adapter.dead_lettered"
                log_json(
                    adapter_logger,
                    failed_event_type,
                    service="drivedesk-worker",
                    adapter_key=exc.adapter_key,
                    outbox_event_id=event.id,
                    tenant_id=event.tenant_id,
                    outbox_event_type=event.event_type,
                    attempt=attempt,
                    duration_ms=duration_ms,
                    retryable=exc.retryable,
                    status=event.status,
                    error=exc.message,
                )
            processed += 1
        return processed


async def main() -> None:
    while True:
        heartbeat = await run_once()
        print(json.dumps(heartbeat, ensure_ascii=False, sort_keys=True), flush=True)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
