from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from drivedesk_api.services import list_pending_outbox, mark_outbox_processed
from drivedesk_api.session import SessionLocal
from drivedesk_api.settings import get_settings
from drivedesk_core import __version__ as core_version


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
        events = await list_pending_outbox(session, limit=limit)
        processed = 0
        for event in events:
            await mark_outbox_processed(session, event)
            processed += 1
        return processed


async def main() -> None:
    while True:
        heartbeat = await run_once()
        print(json.dumps(heartbeat, ensure_ascii=False, sort_keys=True), flush=True)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
