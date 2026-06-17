from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from drivedesk_api.settings import Settings


PROCESS_STARTED_AT = datetime.now(UTC)
PROCESS_STARTED_AT_MONOTONIC = time.monotonic()
HTTP_LATENCY_BUCKETS_SECONDS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_metrics_lock = threading.Lock()
_http_request_counts: dict[tuple[str, str, str], int] = defaultdict(int)
_http_request_latency_buckets: dict[tuple[str, str, str, float], int] = defaultdict(int)
_http_request_latency_counts: dict[tuple[str, str, str], int] = defaultdict(int)
_http_request_latency_sums: dict[tuple[str, str, str], float] = defaultdict(float)


def uptime_seconds() -> float:
    return round(time.monotonic() - PROCESS_STARTED_AT_MONOTONIC, 3)


def build_health_payload(settings: Settings, core_version: str) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "core_version": core_version,
    }


def build_ready_payload(settings: Settings) -> dict[str, object]:
    return {
        "status": "ready",
        "dependencies": {
            "database_url_configured": bool(settings.database_url),
            "redis_url_configured": bool(settings.redis_url),
        },
    }


def prometheus_label_value(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def prometheus_labels(labels: dict[str, object]) -> str:
    rendered = ",".join(f'{key}="{prometheus_label_value(value)}"' for key, value in sorted(labels.items()))
    return "{" + rendered + "}"


def record_http_request(*, method: str, path: str, status_code: int, duration_seconds: float) -> None:
    status = str(status_code)
    base_key = (method, path, status)
    with _metrics_lock:
        _http_request_counts[base_key] += 1
        _http_request_latency_counts[base_key] += 1
        _http_request_latency_sums[base_key] += duration_seconds
        for bucket in HTTP_LATENCY_BUCKETS_SECONDS:
            if duration_seconds <= bucket:
                _http_request_latency_buckets[(*base_key, bucket)] += 1


def route_template_for_scope(scope: dict[str, Any], fallback_path: str) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return fallback_path


def snapshot_http_metrics() -> dict[str, dict]:
    with _metrics_lock:
        return {
            "request_counts": dict(_http_request_counts),
            "latency_buckets": dict(_http_request_latency_buckets),
            "latency_counts": dict(_http_request_latency_counts),
            "latency_sums": dict(_http_request_latency_sums),
        }


def build_http_metrics_lines() -> list[str]:
    snapshot = snapshot_http_metrics()
    lines = [
        "# HELP drivedesk_api_http_requests_total Total HTTP requests handled by the DriveDesk API.",
        "# TYPE drivedesk_api_http_requests_total counter",
    ]
    for (method, path, status), count in sorted(snapshot["request_counts"].items()):
        labels = prometheus_labels({"method": method, "path": path, "status_code": status})
        lines.append(f"drivedesk_api_http_requests_total{labels} {count}")

    lines.extend(
        [
            "# HELP drivedesk_api_http_request_duration_seconds HTTP request duration in seconds.",
            "# TYPE drivedesk_api_http_request_duration_seconds histogram",
        ]
    )
    for method, path, status in sorted(snapshot["latency_counts"]):
        cumulative = 0
        for bucket in HTTP_LATENCY_BUCKETS_SECONDS:
            cumulative = snapshot["latency_buckets"].get((method, path, status, bucket), cumulative)
            labels = prometheus_labels({"method": method, "path": path, "status_code": status, "le": f"{bucket:g}"})
            lines.append(f"drivedesk_api_http_request_duration_seconds_bucket{labels} {cumulative}")
        count = snapshot["latency_counts"][(method, path, status)]
        sum_value = snapshot["latency_sums"][(method, path, status)]
        inf_labels = prometheus_labels({"method": method, "path": path, "status_code": status, "le": "+Inf"})
        base_labels = prometheus_labels({"method": method, "path": path, "status_code": status})
        lines.append(f"drivedesk_api_http_request_duration_seconds_bucket{inf_labels} {count}")
        lines.append(f"drivedesk_api_http_request_duration_seconds_count{base_labels} {count}")
        lines.append(f"drivedesk_api_http_request_duration_seconds_sum{base_labels} {sum_value:.6f}")
    return lines


def build_outbox_metrics_lines(outbox_counts: dict[str, int]) -> list[str]:
    lines = [
        "# HELP drivedesk_outbox_events Current outbox events by status.",
        "# TYPE drivedesk_outbox_events gauge",
    ]
    for status, count in sorted(outbox_counts.items()):
        labels = prometheus_labels({"status": status})
        lines.append(f"drivedesk_outbox_events{labels} {count}")
    return lines


def build_readiness_metrics_lines(settings: Settings) -> list[str]:
    dependencies = {
        "database_url_configured": bool(settings.database_url),
        "redis_url_configured": bool(settings.redis_url),
    }
    dependencies["all"] = all(dependencies.values())

    lines = [
        "# HELP drivedesk_api_readiness DriveDesk API readiness dependencies as 1 for ready and 0 for not ready.",
        "# TYPE drivedesk_api_readiness gauge",
    ]
    for dependency, is_ready in sorted(dependencies.items()):
        labels = prometheus_labels({"dependency": dependency})
        lines.append(f"drivedesk_api_readiness{labels} {1 if is_ready else 0}")
    return lines


def build_metrics_text(settings: Settings, core_version: str, outbox_counts: dict[str, int] | None = None) -> str:
    labels = prometheus_labels(
        {
            "service": settings.service_name,
            "environment": settings.environment,
            "core_version": core_version,
        }
    )
    started_at = PROCESS_STARTED_AT.isoformat()
    lines = [
        "# HELP drivedesk_api_info DriveDesk API build and environment info.",
        "# TYPE drivedesk_api_info gauge",
        f"drivedesk_api_info{labels} 1",
        "# HELP drivedesk_api_uptime_seconds DriveDesk API process uptime in seconds.",
        "# TYPE drivedesk_api_uptime_seconds gauge",
        f"drivedesk_api_uptime_seconds {uptime_seconds()}",
        "# HELP drivedesk_api_started_at_seconds DriveDesk API process start time as Unix timestamp.",
        "# TYPE drivedesk_api_started_at_seconds gauge",
        f"drivedesk_api_started_at_seconds {PROCESS_STARTED_AT.timestamp()}",
        "# HELP drivedesk_api_started_at_info DriveDesk API process start time info.",
        "# TYPE drivedesk_api_started_at_info gauge",
        f'drivedesk_api_started_at_info{{started_at="{prometheus_label_value(started_at)}"}} 1',
    ]
    lines.extend(build_readiness_metrics_lines(settings))
    lines.extend(build_http_metrics_lines())
    lines.extend(build_outbox_metrics_lines(outbox_counts or {}))
    lines.append("")
    return "\n".join(lines)


def log_json(logger: logging.Logger, event_type: str, **fields: Any) -> None:
    payload = {
        "event_type": event_type,
        "observed_at": datetime.now(UTC).isoformat(),
        **fields,
    }
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
