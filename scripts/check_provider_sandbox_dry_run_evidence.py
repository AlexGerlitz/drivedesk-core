#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SAFE_STATUSES = {
    "ready_for_private_read_only_dry_run",
    "private_read_only_dry_run_completed",
    "private_read_only_dry_run_retryable_failure",
    "private_read_only_dry_run_rejected",
}

COMPLETED_STATUS = "private_read_only_dry_run_completed"

LEAK_PATTERNS = {
    "raw_provider_url": re.compile(r"https?://[^\s\"']+/rest/[^\s\"']+", re.IGNORECASE),
    "bitrix_webhook_token": re.compile(r"/rest/\d+/[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "russian_phone": re.compile(r"(?:\+7|8)[\s(.-]*\d{3}[\s). -]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}"),
    "provider_deal_id": re.compile(r"DEAL[-_][A-Za-z0-9_-]+", re.IGNORECASE),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"evidence file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"evidence file is not valid JSON: {path}") from exc
    _require(isinstance(payload, dict), "evidence payload must be a JSON object")
    return payload


def _bool_is_false(payload: Mapping[str, Any], key: str) -> bool:
    return payload.get(key) is False


def _missing_or_false(payload: Mapping[str, Any], key: str) -> bool:
    return key not in payload or payload.get(key) is False


def _scan_for_leaks(serialized: str) -> None:
    for name, pattern in LEAK_PATTERNS.items():
        _require(not pattern.search(serialized), f"evidence leaked {name}")


def validate_provider_sandbox_dry_run_evidence(
    path: Path,
    *,
    require_completed: bool = False,
) -> dict[str, Any]:
    payload = _load_json(path)
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    status = str(payload.get("status") or "")
    if require_completed:
        _require(status == COMPLETED_STATUS, "evidence status must be completed")
    else:
        _require(status in SAFE_STATUSES, f"unsupported evidence status: {status}")

    request_plan = payload.get("request_plan")
    _require(isinstance(request_plan, dict), "request_plan must be present")
    operation = payload.get("operation") or request_plan.get("operation")

    _require(payload.get("adapter_key") == "crm.bitrix24.mock", "unexpected adapter key")
    _require(operation == "crm.deal.list", "unexpected provider operation")
    _require(payload.get("dry_run_mode") == "read_only", "dry-run mode must stay read_only")
    _require(_bool_is_false(payload, "external_mutation"), "external mutation must be false")
    _require(_bool_is_false(payload, "raw_payload_included"), "raw payload must not be included")
    _require(_missing_or_false(payload, "request_body_included"), "request body must not be included")
    _require(_missing_or_false(payload, "provider_endpoint_included"), "provider endpoint must not be included")
    _require(_bool_is_false(payload, "contains_pii"), "PII marker must be false")
    _require(_bool_is_false(payload, "secret_values_included"), "secret values must not be included")

    _require(request_plan.get("operation") == "crm.deal.list", "request plan operation mismatch")
    _require(request_plan.get("max_page_size") == 5, "request plan page size must stay bounded")
    _require(request_plan.get("timeout_seconds") == 10, "request plan timeout must stay bounded")
    _require(request_plan.get("external_mutation") is False, "request plan mutation must be false")

    operator_cli = payload.get("operator_cli")
    _require(isinstance(operator_cli, dict), "operator_cli metadata must be present")
    _require(
        operator_cli.get("script") == "scripts/run_provider_sandbox_dry_run.py",
        "operator CLI script mismatch",
    )
    _require(
        operator_cli.get("mode") in {"plan_only", "execute_read_only"},
        "operator CLI mode mismatch",
    )
    _require(operator_cli.get("secret_values_included") is False, "operator CLI leaked secret flag")
    _require(
        operator_cli.get("raw_provider_payload_included") is False,
        "operator CLI raw payload flag mismatch",
    )

    if status == COMPLETED_STATUS:
        _require(payload.get("records_received", -1) >= 0, "records_received must be non-negative")
        _require(payload.get("records_accepted", -1) >= 0, "records_accepted must be non-negative")
        _require(payload.get("records_rejected", -1) >= 0, "records_rejected must be non-negative")
        _require(payload.get("reconciliation_probe_attached") is True, "reconciliation probe missing")
        _require(payload.get("failure") is None, "completed dry-run must not include failure")
    else:
        failure = payload.get("failure")
        if failure is not None:
            _require(isinstance(failure, dict), "failure must be a JSON object when present")
            _require(
                failure.get("error_message_included") is not True,
                "failure must not include provider exception message",
            )
            _require(
                failure.get("provider_error_description_included") is not True,
                "failure must not include provider error description",
            )

    _scan_for_leaks(serialized)
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate sanitized DriveDesk provider sandbox dry-run evidence.",
    )
    parser.add_argument("evidence_file", type=Path)
    parser.add_argument(
        "--require-completed",
        action="store_true",
        help="Require private_read_only_dry_run_completed status.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    payload = validate_provider_sandbox_dry_run_evidence(
        args.evidence_file,
        require_completed=args.require_completed,
    )
    print(
        "provider sandbox dry-run evidence ok: "
        f"status={payload['status']} operation={payload.get('operation') or payload['request_plan']['operation']}"
    )


if __name__ == "__main__":
    main()
