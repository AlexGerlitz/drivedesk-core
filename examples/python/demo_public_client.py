from __future__ import annotations

import json
import os
import urllib.request


def main() -> None:
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    url = f"{base_url}/demo/public"

    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    assert payload["schemaVersion"] == 1
    assert payload["dataSource"] == "api.synthetic"
    assert payload["apiContract"]["path"] == "/demo/public"
    assert payload["tenant"]["slug"] == "demo-academy"
    assert payload["workflow"]["id"] == "wf-demo-lead-to-student"
    assert payload["workflow"]["currentStage"] == "student_sync"
    assert len(payload["workflow"]["stages"]) >= 5

    print(
        "python demo client ok:",
        payload["tenant"]["slug"],
        payload["dataSource"],
        f"workflow={payload['workflow']['currentStage']}",
        f"metrics={len(payload['metrics'])}",
    )


if __name__ == "__main__":
    main()
