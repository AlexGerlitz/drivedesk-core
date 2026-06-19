#!/usr/bin/env node
import { pathToFileURL } from "node:url";

export const PUBLIC_DEMO_PATH = "/demo/public";
export const OPERATION_ID = "public_demo_demo_public_get";
export const REQUIRED_FIELDS = [
  "schemaVersion",
  "generatedAt",
  "dataSource",
  "apiContract",
  "tenant",
  "health",
  "metrics",
  "workQueue",
  "members",
  "auditEvents",
  "outbox",
  "adapters",
  "adapterScenarios",
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "recoveryEvidence",
  "alertRouting",
  "incidentResponse",
  "businessControlTower",
  "engineeringProof",
  "workflow",
  "workflowScenarios",
  "endToEndScenario",
  "timeline",
  "domainEvents"
];

export class DriveDeskPublicDemoClient {
  constructor(baseUrl = "http://localhost:8080", options = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    if (!this.fetchImpl) {
      throw new Error("fetch is not available in this JavaScript runtime");
    }
  }

  async getPublicDemo() {
    const response = await this.fetchImpl(`${this.baseUrl}${PUBLIC_DEMO_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${PUBLIC_DEMO_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validatePublicDemoPayload(payload);
    return payload;
  }

  async getAdapterOperationPlan(scenarioId, options = {}) {
    const payload = await this.getPublicDemo();
    return buildAdapterOperationPlan(payload, scenarioId, options);
  }
}

export function getAdapterScenario(payload, scenarioId) {
  if (!Array.isArray(payload.adapterScenarios)) {
    throw new Error("adapterScenarios is missing");
  }

  const scenario = payload.adapterScenarios.find((item) => item?.id === scenarioId);
  if (!scenario) {
    throw new Error(`unknown adapter scenario: ${scenarioId}`);
  }

  return scenario;
}

export function buildAdapterOperationPlan(payload, scenarioId, options = {}) {
  validatePublicDemoPayload(payload);
  const scenario = getAdapterScenario(payload, scenarioId);
  const [method, path] = splitAdapterEndpoint(scenario.endpoint);
  const requestId = options.requestId || "demo-request-001";
  const headers = {
    Accept: "application/json",
    "X-DriveDesk-Tenant": payload.tenant?.slug || "demo-academy",
  };

  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    headers["Idempotency-Key"] = `${scenarioId}:${requestId}`;
  }

  return {
    scenarioId,
    adapter: scenario.adapter,
    operation: scenario.operation,
    phase: scenario.phase,
    executionMode: "contract_only",
    safeToRunAgainstPublicDemo: false,
    request: {
      method,
      path,
      headers,
      body: adapterOperationBody(scenario, requestId),
    },
    expectedResponse: {
      status: scenario.status,
      outputs: [...(scenario.outputs || [])],
      evidence: scenario.evidence,
      sideEffects: adapterSideEffects(scenario),
    },
  };
}

function splitAdapterEndpoint(endpoint) {
  if (String(endpoint || "").startsWith("worker:")) {
    return ["WORKER", endpoint];
  }
  const match = /^(GET|POST|PUT|PATCH|DELETE)\s+(.+)$/.exec(String(endpoint || "").trim());
  if (!match) {
    throw new Error(`invalid adapter endpoint contract: ${endpoint}`);
  }
  return [match[1], match[2]];
}

function adapterOperationBody(scenario, requestId) {
  const base = {
    requestId,
    scenarioId: scenario.id,
    operation: scenario.operation,
  };

  if (scenario.operation === "crm_deal_intake_preview") {
    return {
      ...base,
      dryRun: true,
      provider_key: "crm.bitrix24.mock",
      source_type: "crm_deal",
      subject_type: "deal",
      subject_id: "DEAL-2026-001",
      external_ref: "crm-deal-001",
      provider_payload: {
        stage: "invoice_sent",
        amount: 1500,
        owner_role: "sales",
        full_name: "Synthetic Customer",
        phone: "+70000000000",
        access_token: "never-return-this",
      },
    };
  }

  if (scenario.operation === "crm_deal_ingest_execute") {
    return {
      ...base,
      dryRun: false,
      batch_id: "bitrix_demo_batch",
      mapping: {
        deal_id: "ID",
        source_state: "STAGE_ID",
        owner_role: "ASSIGNED_BY_ROLE",
        amount: "OPPORTUNITY",
      },
      deals: [
        {
          ID: "DEAL-2026-001",
          STAGE_ID: "invoice_sent",
          ASSIGNED_BY_ROLE: "sales",
          OPPORTUNITY: 1500,
        },
      ],
      confirm: true,
    };
  }

  if (scenario.phase === "preview") {
    return {
      ...base,
      dryRun: true,
      mappingProfile: "public-demo-v1",
      sourceRef: "synthetic-file-import",
      sampleRows: [
        { externalId: "lead-001", personRef: "person-demo-001", courseRef: "course-b" },
      ],
    };
  }

  if (scenario.phase === "execute") {
    return {
      ...base,
      dryRun: false,
      previewId: "preview-demo-001",
      confirm: true,
    };
  }

  if (scenario.phase === "retry") {
    return {
      ...base,
      failedJobId: "job-demo-retry-001",
      retryMode: "same_payload",
      attempt: 3,
    };
  }

  if (scenario.phase === "operator_review") {
    return null;
  }

  throw new Error(`unsupported adapter scenario phase: ${scenario.phase}`);
}

function adapterSideEffects(scenario) {
  const outputs = new Set(scenario.outputs || []);
  const sideEffects = [];
  if (outputs.has("mapping_preview")) {
    sideEffects.push("validates mapping without creating outbox events");
  }
  if (outputs.has("outbox_event")) {
    sideEffects.push("creates outbox event for asynchronous adapter processing");
  }
  if (outputs.has("adapter_job")) {
    sideEffects.push("records adapter job status for operator visibility");
  }
  if (outputs.has("retry_scheduled")) {
    sideEffects.push("schedules retry with bounded attempt tracking");
  }
  if (outputs.has("review_card")) {
    sideEffects.push("creates operator review card for dead-letter handling");
  }
  return sideEffects;
}

export function validatePublicDemoPayload(payload) {
  const missing = REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {
    throw new Error(`missing required fields: ${missing.join(", ")}`);
  }

  if (payload.schemaVersion !== 1) {
    throw new Error(`unexpected schemaVersion: ${payload.schemaVersion}`);
  }

  if (payload.dataSource !== "api.synthetic") {
    throw new Error(`unexpected dataSource: ${payload.dataSource}`);
  }

  if (payload.apiContract?.path !== PUBLIC_DEMO_PATH) {
    throw new Error(`unexpected apiContract.path: ${payload.apiContract?.path}`);
  }

  if (payload.tenant?.slug !== "demo-academy") {
    throw new Error(`unexpected tenant.slug: ${payload.tenant?.slug}`);
  }

  if (payload.workflow?.id !== "wf-demo-lead-to-student") {
    throw new Error(`unexpected workflow.id: ${payload.workflow?.id}`);
  }

  if (payload.workflow?.currentStage !== "student_sync") {
    throw new Error(`unexpected workflow.currentStage: ${payload.workflow?.currentStage}`);
  }

  if (!Array.isArray(payload.workflow?.stages) || payload.workflow.stages.length < 5) {
    throw new Error("workflow.stages is missing or too short");
  }

  if (!Array.isArray(payload.workflowScenarios) || payload.workflowScenarios.length < 3) {
    throw new Error("workflowScenarios is missing or too short");
  }

  const scenarioIds = new Set(payload.workflowScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of ["scenario-contract-approval-sync", "scenario-signature-task", "scenario-accounting-export"]) {
    if (!scenarioIds.has(requiredScenario)) {
      throw new Error(`workflowScenarios does not include required scenario: ${requiredScenario}`);
    }
  }

  const actionTypes = new Set(payload.workflowScenarios.map((scenario) => scenario?.actionType));
  for (const requiredAction of ["emit_outbox_event", "create_task_record", "request_adapter_sync"]) {
    if (!actionTypes.has(requiredAction)) {
      throw new Error(`workflowScenarios does not include required action: ${requiredAction}`);
    }
  }

  const scenarioOutputs = new Set(payload.workflowScenarios.flatMap((scenario) => scenario?.outputs || []));
  for (const requiredOutput of ["audit_event", "outbox_event", "task_record", "integration_job", "action_run"]) {
    if (!scenarioOutputs.has(requiredOutput)) {
      throw new Error(`workflowScenarios does not include required output: ${requiredOutput}`);
    }
  }

  if (!Array.isArray(payload.adapterScenarios) || payload.adapterScenarios.length < 6) {
    throw new Error("adapterScenarios is missing or too short");
  }

  const adapterScenarioIds = new Set(payload.adapterScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of [
    "adapter-file-import-preview",
    "adapter-file-import-execute",
    "adapter-crm-deal-preview",
    "adapter-crm-deal-ingest",
    "adapter-accounting-export-retry",
    "adapter-dead-letter-review",
  ]) {
    if (!adapterScenarioIds.has(requiredScenario)) {
      throw new Error(`adapterScenarios does not include required scenario: ${requiredScenario}`);
    }
  }

  const adapterPhases = new Set(payload.adapterScenarios.map((scenario) => scenario?.phase));
  for (const requiredPhase of ["preview", "execute", "retry", "operator_review"]) {
    if (!adapterPhases.has(requiredPhase)) {
      throw new Error(`adapterScenarios does not include required phase: ${requiredPhase}`);
    }
  }

  const adapterOutputs = new Set(payload.adapterScenarios.flatMap((scenario) => scenario?.outputs || []));
  for (const requiredOutput of [
    "mapping_preview",
    "outbox_event",
    "adapter_job",
    "safe_payload",
    "normalized_observation",
    "no_provider_call",
    "redaction_evidence",
    "retry_scheduled",
    "review_card",
    "manual_retry_endpoint",
  ]) {
    if (!adapterOutputs.has(requiredOutput)) {
      throw new Error(`adapterScenarios does not include required output: ${requiredOutput}`);
    }
  }

  if (payload.engineeringProof?.milestone !== "engineering_70") {
    throw new Error(`unexpected engineeringProof.milestone: ${payload.engineeringProof?.milestone}`);
  }

  if (!Array.isArray(payload.engineeringProof?.gates) || payload.engineeringProof.gates.length < 5) {
    throw new Error("engineeringProof.gates is missing or too short");
  }

  if (!Array.isArray(payload.alertRouting?.routes) || payload.alertRouting.routes.length < 3) {
    throw new Error("alertRouting.routes is missing or too short");
  }

  if (!Array.isArray(payload.alertRouting?.bindings) || payload.alertRouting.bindings.length < 5) {
    throw new Error("alertRouting.bindings is missing or too short");
  }

  const alertNames = new Set(payload.alertRouting.bindings.map((binding) => binding?.alert));
  for (const requiredAlert of ["DriveDeskApiTargetDown", "DriveDeskIntegrationDeadLetters", "DriveDeskScheduledValidationMissed"]) {
    if (!alertNames.has(requiredAlert)) {
      throw new Error(`alertRouting.bindings does not include required alert: ${requiredAlert}`);
    }
  }

  if (!Array.isArray(payload.incidentResponse?.incidents) || payload.incidentResponse.incidents.length < 3) {
    throw new Error("incidentResponse.incidents is missing or too short");
  }

  const incidentStatuses = new Set(payload.incidentResponse.incidents.map((incident) => incident?.status));
  for (const requiredStatus of ["open", "acknowledged", "resolved"]) {
    if (!incidentStatuses.has(requiredStatus)) {
      throw new Error(`incidentResponse.incidents does not include required status: ${requiredStatus}`);
    }
  }

  if (!Array.isArray(payload.incidentResponse?.timeline) || payload.incidentResponse.timeline.length < 5) {
    throw new Error("incidentResponse.timeline is missing or too short");
  }

  if (!Array.isArray(payload.domainEvents)) {
    throw new Error("domainEvents is missing");
  }

  const eventNames = new Set(payload.domainEvents.map((event) => event?.event));
  for (const requiredEvent of ["lead.created", "student.created", "contract.generated", "student.sync.requested"]) {
    if (!eventNames.has(requiredEvent)) {
      throw new Error(`domainEvents does not include required event: ${requiredEvent}`);
    }
  }
}

async function main() {
  const baseUrlIndex = process.argv.indexOf("--base-url");
  const baseUrl =
    baseUrlIndex >= 0 && process.argv[baseUrlIndex + 1]
      ? process.argv[baseUrlIndex + 1]
      : process.env.BASE_URL || "http://localhost:8080";
  const client = new DriveDeskPublicDemoClient(baseUrl);
  const payload = await client.getPublicDemo();
  const adapterPlan = buildAdapterOperationPlan(payload, "adapter-file-import-preview");
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${payload.workflow.currentStage}`,
    `adapterPlan=${adapterPlan.phase}`,
    `operation=${OPERATION_ID}`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
