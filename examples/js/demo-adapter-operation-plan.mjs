import { DriveDeskPublicDemoClient } from "../../sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs";

async function main() {
  const baseUrl = (process.env.BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
  const client = new DriveDeskPublicDemoClient(baseUrl);
  const plan = await client.getAdapterOperationPlan("adapter-file-import-preview", {
    requestId: "example-preview-001",
  });

  if (plan.executionMode !== "contract_only") {
    throw new Error(`unexpected executionMode: ${plan.executionMode}`);
  }

  if (plan.safeToRunAgainstPublicDemo !== false) {
    throw new Error("public demo adapter plan must be contract-only");
  }

  if (plan.phase !== "preview") {
    throw new Error(`unexpected phase: ${plan.phase}`);
  }

  if (plan.request.method !== "POST") {
    throw new Error(`unexpected method: ${plan.request.method}`);
  }

  if (plan.request.headers["Idempotency-Key"] !== "adapter-file-import-preview:example-preview-001") {
    throw new Error(`unexpected idempotency key: ${plan.request.headers["Idempotency-Key"]}`);
  }

  if (plan.request.body?.dryRun !== true) {
    throw new Error("preview request must be dry-run");
  }

  if (!plan.expectedResponse.outputs.includes("mapping_preview")) {
    throw new Error("preview response plan must include mapping_preview");
  }

  console.log(
    "js adapter plan ok:",
    plan.scenarioId,
    plan.request.method,
    plan.phase,
    plan.executionMode,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
