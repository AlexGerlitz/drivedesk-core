from __future__ import annotations

import os
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SDK_PATH = ROOT / "sdk/generated/public-demo/python"
sys.path.insert(0, str(SDK_PATH))

from drivedesk_public_demo_client import DriveDeskPublicDemoClient


def main() -> None:
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    client = DriveDeskPublicDemoClient(base_url)
    plan = client.get_adapter_operation_plan(
        "adapter-file-import-preview",
        request_id="example-preview-001",
    )

    assert plan["executionMode"] == "contract_only"
    assert plan["safeToRunAgainstPublicDemo"] is False
    assert plan["phase"] == "preview"
    assert plan["request"]["method"] == "POST"
    assert plan["request"]["headers"]["Idempotency-Key"] == (
        "adapter-file-import-preview:example-preview-001"
    )
    assert plan["request"]["body"]["dryRun"] is True
    assert "mapping_preview" in plan["expectedResponse"]["outputs"]

    print(
        "python adapter plan ok:",
        plan["scenarioId"],
        plan["request"]["method"],
        plan["phase"],
        plan["executionMode"],
    )


if __name__ == "__main__":
    main()
