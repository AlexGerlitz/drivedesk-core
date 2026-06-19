import { DriveDeskPublicDemoClient } from "../../sdk/generated/public-demo/javascript/drivedesk-public-demo-client.mjs";

async function main() {
  const baseUrl = (process.env.BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
  const client = new DriveDeskPublicDemoClient(baseUrl);
  const plan = await client.getAdapterOperationPlan("adapter-file-import-preview", {
    requestId: "example-preview-001",
  });
  const crmPlan = await client.getAdapterOperationPlan("adapter-crm-deal-preview", {
    requestId: "example-crm-preview-001",
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

  if (crmPlan.executionMode !== "contract_only") {
    throw new Error(`unexpected CRM executionMode: ${crmPlan.executionMode}`);
  }

  if (crmPlan.safeToRunAgainstPublicDemo !== false) {
    throw new Error("CRM public demo adapter plan must be contract-only");
  }

  if (crmPlan.adapter !== "crm.bitrix24.mock") {
    throw new Error(`unexpected CRM adapter: ${crmPlan.adapter}`);
  }

  if (crmPlan.operation !== "crm_deal_intake_preview") {
    throw new Error(`unexpected CRM operation: ${crmPlan.operation}`);
  }

  if (crmPlan.phase !== "preview") {
    throw new Error(`unexpected CRM phase: ${crmPlan.phase}`);
  }

  if (crmPlan.request.method !== "POST") {
    throw new Error(`unexpected CRM method: ${crmPlan.request.method}`);
  }

  if (crmPlan.request.path !== "/tenants/{tenant_id}/business-provider-intake/preview") {
    throw new Error(`unexpected CRM path: ${crmPlan.request.path}`);
  }

  if (crmPlan.request.headers["Idempotency-Key"] !== "adapter-crm-deal-preview:example-crm-preview-001") {
    throw new Error(`unexpected CRM idempotency key: ${crmPlan.request.headers["Idempotency-Key"]}`);
  }

  if (crmPlan.request.body?.provider_key !== "crm.bitrix24.mock") {
    throw new Error("CRM plan must target crm.bitrix24.mock provider_key");
  }

  if (crmPlan.request.body?.source_type !== "crm_deal") {
    throw new Error("CRM plan must use crm_deal source_type");
  }

  if (crmPlan.request.body?.provider_payload?.access_token !== "never-return-this") {
    throw new Error("CRM plan must show redaction-test token in contract-only body");
  }

  for (const output of ["safe_payload", "normalized_observation", "no_provider_call"]) {
    if (!crmPlan.expectedResponse.outputs.includes(output)) {
      throw new Error(`CRM response plan must include ${output}`);
    }
  }

  console.log(
    "js adapter plan ok:",
    plan.scenarioId,
    plan.request.method,
    plan.phase,
    plan.executionMode,
    `crm=${crmPlan.operation}`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
