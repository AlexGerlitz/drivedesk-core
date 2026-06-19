#!/usr/bin/env node
import { pathToFileURL } from "node:url";

export const PUBLIC_DEMO_PATH = "/demo/public";
export const CONNECTOR_REPLAY_PATH = "/demo/connector-fixture-replay";
export const CONNECTOR_CERTIFICATION_PATH = "/demo/connector-certification";
export const PROVIDER_ONBOARDING_PATH = "/demo/provider-onboarding";
export const INTEGRATION_REPAIR_PATH = "/demo/integration-repair";
export const OBSERVABILITY_DASHBOARD_PATH = "/demo/observability-dashboard";
export const BUSINESS_SCENARIO_REPLAY_PATH = "/demo/business-scenario-replay";
export const OPERATION_ID = "public_demo_demo_public_get";
export const CONNECTOR_REPLAY_OPERATION_ID = "connector_fixture_replay_demo_demo_connector_fixture_replay_get";
export const CONNECTOR_CERTIFICATION_OPERATION_ID = "connector_certification_demo_demo_connector_certification_get";
export const PROVIDER_ONBOARDING_OPERATION_ID = "provider_onboarding_demo_demo_provider_onboarding_get";
export const INTEGRATION_REPAIR_OPERATION_ID = "integration_repair_demo_demo_integration_repair_get";
export const OBSERVABILITY_DASHBOARD_OPERATION_ID = "observability_dashboard_demo_demo_observability_dashboard_get";
export const BUSINESS_SCENARIO_REPLAY_OPERATION_ID = "business_scenario_replay_demo_demo_business_scenario_replay_get";
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
  "adapterStudio",
  "connectorCertification",
  "providerOnboarding",
  "integrationRuntime",
  "integrationExecution",
  "integrationRepair",
  "observabilityDashboard",
  "notificationDelivery",
  "connectorFixtureReplay",
  "businessIntakePipeline",
  "businessTaskHandoff",
  "businessNotificationChannels",
  "businessContextAssistant",
  "businessActionExecution",
  "businessApprovalGateway",
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "recoveryEvidence",
  "alertRouting",
  "incidentResponse",
  "businessControlTower",
  "businessScenarioReplay",
  "engineeringProof",
  "workflow",
  "workflowScenarios",
  "endToEndScenario",
  "timeline",
  "domainEvents"
];
export const CONNECTOR_REPLAY_REQUIRED_FIELDS = [
  "status",
  "command",
  "fixtureFile",
  "evidenceFile",
  "summary",
  "outcomes",
  "boundaries",
  "docs"
];
export const CONNECTOR_CERTIFICATION_REQUIRED_FIELDS = [
  "status",
  "command",
  "certificationLevel",
  "adapterCount",
  "privateReadyCount",
  "summary",
  "providerProfiles",
  "certificationStages",
  "certificationGates",
  "implementationPath",
  "dataBoundaries",
  "api",
  "docs"
];
export const PROVIDER_ONBOARDING_REQUIRED_FIELDS = [
  "status",
  "command",
  "onboardingLevel",
  "providerKey",
  "providerName",
  "providerCategory",
  "summary",
  "providerProfile",
  "onboardingStages",
  "mappingPreview",
  "preflightChecks",
  "sandboxContract",
  "rolloutPlan",
  "dataBoundaries",
  "api",
  "docs"
];
export const INTEGRATION_REPAIR_REQUIRED_FIELDS = [
  "status",
  "command",
  "repairLevel",
  "incidentCount",
  "criticalCount",
  "safeActionCount",
  "summary",
  "incidentMatrix",
  "repairRunbooks",
  "impactAnalysis",
  "repairActions",
  "safeExecutionPlan",
  "dataBoundaries",
  "api",
  "docs"
];
export const OBSERVABILITY_DASHBOARD_REQUIRED_FIELDS = [
  "status",
  "command",
  "dashboardLevel",
  "summary",
  "dashboardGroups",
  "panelCatalog",
  "queryExamples",
  "alertLinks",
  "dataBoundaries",
  "api",
  "docs"
];
export const BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS = [
  "status",
  "command",
  "summary",
  "scenarios",
  "flow",
  "docs"
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

  async getConnectorFixtureReplay() {
    const response = await this.fetchImpl(`${this.baseUrl}${CONNECTOR_REPLAY_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${CONNECTOR_REPLAY_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateConnectorFixtureReplayPayload(payload);
    return payload;
  }

  async getConnectorCertification() {
    const response = await this.fetchImpl(`${this.baseUrl}${CONNECTOR_CERTIFICATION_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${CONNECTOR_CERTIFICATION_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateConnectorCertificationPayload(payload);
    return payload;
  }

  async getProviderOnboarding() {
    const response = await this.fetchImpl(`${this.baseUrl}${PROVIDER_ONBOARDING_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${PROVIDER_ONBOARDING_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateProviderOnboardingPayload(payload);
    return payload;
  }

  async getIntegrationRepair() {
    const response = await this.fetchImpl(`${this.baseUrl}${INTEGRATION_REPAIR_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${INTEGRATION_REPAIR_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateIntegrationRepairPayload(payload);
    return payload;
  }

  async getObservabilityDashboard() {
    const response = await this.fetchImpl(`${this.baseUrl}${OBSERVABILITY_DASHBOARD_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${OBSERVABILITY_DASHBOARD_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateObservabilityDashboardPayload(payload);
    return payload;
  }

  async getBusinessScenarioReplay() {
    const response = await this.fetchImpl(`${this.baseUrl}${BUSINESS_SCENARIO_REPLAY_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${BUSINESS_SCENARIO_REPLAY_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validateBusinessScenarioReplayPayload(payload);
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

export function validateConnectorFixtureReplayPayload(payload) {
  const missing = CONNECTOR_REPLAY_REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {
    throw new Error(`missing connector fixture replay fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "validated") {
    throw new Error(`unexpected connector replay status: ${payload.status}`);
  }

  if (payload.command !== "bash scripts/check_public_connector_fixture_replay.sh") {
    throw new Error(`unexpected connector replay command: ${payload.command}`);
  }

  if (payload.fixtureFile !== "examples/connector-fixtures/replay-fixtures.sanitized.json") {
    throw new Error(`unexpected connector replay fixtureFile: ${payload.fixtureFile}`);
  }

  if (!Array.isArray(payload.outcomes) || payload.outcomes.length < 6) {
    throw new Error("connector replay outcomes are missing or too short");
  }

  const groups = new Set(payload.outcomes.map((item) => item?.group));
  const requiredGroups = [
    "happy_path_preview",
    "sensitive_payload_redaction",
    "invalid_payload",
    "retryable_provider_failure",
    "dead_letter_provider_failure",
    "reconciliation_mismatch",
  ];
  for (const group of requiredGroups) {
    if (!groups.has(group)) {
      throw new Error(`connector replay group is missing: ${group}`);
    }
  }

  if (!Array.isArray(payload.boundaries) || payload.boundaries.length < 4) {
    throw new Error("connector replay boundaries are missing or too short");
  }

  const boundaryNames = new Set(payload.boundaries.map((item) => item?.name));
  for (const boundary of ["raw payload", "credentials", "external calls", "persistence"]) {
    if (!boundaryNames.has(boundary)) {
      throw new Error(`connector replay boundary is missing: ${boundary}`);
    }
  }

  if (!Array.isArray(payload.docs) || payload.docs.length < 3) {
    throw new Error("connector replay docs are missing or too short");
  }
}

export function validateConnectorCertificationPayload(payload) {
  const missing = CONNECTOR_CERTIFICATION_REQUIRED_FIELDS.filter((field) => !(field in (payload || {})));
  if (missing.length > 0) {
    throw new Error(`missing connector certification fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "validated") {
    throw new Error(`unexpected connector certification status: ${payload.status}`);
  }

  if (payload.command !== `GET ${CONNECTOR_CERTIFICATION_PATH}`) {
    throw new Error(`unexpected connector certification command: ${payload.command}`);
  }

  if (payload.certificationLevel !== "public_contract_certified") {
    throw new Error(`unexpected connector certification level: ${payload.certificationLevel}`);
  }

  if (!Array.isArray(payload.providerProfiles) || payload.providerProfiles.length < 3) {
    throw new Error("connector certification provider profiles are missing or too short");
  }

  const providerKeys = new Set(payload.providerProfiles.map((item) => item?.adapterKey));
  for (const requiredKey of ["crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"]) {
    if (!providerKeys.has(requiredKey)) {
      throw new Error(`connector certification provider key missing: ${requiredKey}`);
    }
  }

  if (!Array.isArray(payload.certificationStages) || payload.certificationStages.length < 6) {
    throw new Error("connector certification stages are missing or too short");
  }

  if (!Array.isArray(payload.certificationGates) || payload.certificationGates.length < 5) {
    throw new Error("connector certification gates are missing or too short");
  }

  if (payload.certificationGates.some((item) => item?.externalMutation !== false)) {
    throw new Error("connector certification gates must not mutate external providers");
  }

  if (!Array.isArray(payload.dataBoundaries) || payload.dataBoundaries.length < 3) {
    throw new Error("connector certification data boundaries are missing or too short");
  }
}

export function validateProviderOnboardingPayload(payload) {
  const missing = PROVIDER_ONBOARDING_REQUIRED_FIELDS.filter((field) => !(field in (payload || {})));
  if (missing.length > 0) {
    throw new Error(`missing provider onboarding fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "previewed") {
    throw new Error(`unexpected provider onboarding status: ${payload.status}`);
  }

  if (payload.command !== `GET ${PROVIDER_ONBOARDING_PATH}`) {
    throw new Error(`unexpected provider onboarding command: ${payload.command}`);
  }

  if (payload.onboardingLevel !== "sandbox_onboarding_ready") {
    throw new Error(`unexpected provider onboarding level: ${payload.onboardingLevel}`);
  }

  if (payload.providerKey !== "crm.bitrix24.mock") {
    throw new Error(`unexpected provider onboarding key: ${payload.providerKey}`);
  }

  for (const key of ["summary", "onboardingStages", "preflightChecks", "rolloutPlan", "dataBoundaries"]) {
    if (!Array.isArray(payload[key]) || payload[key].length === 0) {
      throw new Error(`provider onboarding ${key} is missing or empty`);
    }
  }

  if (!payload.sandboxContract || payload.sandboxContract.providerCallEnabled !== false) {
    throw new Error("provider onboarding sandbox contract must not call providers");
  }

  if (payload.dataBoundaries.some((item) => item?.externalMutation !== false)) {
    throw new Error("provider onboarding boundaries must not mutate external providers");
  }
}

export function validateIntegrationRepairPayload(payload) {
  const missing = INTEGRATION_REPAIR_REQUIRED_FIELDS.filter((field) => !(field in (payload || {})));
  if (missing.length > 0) {
    throw new Error(`missing integration repair fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "previewed") {
    throw new Error(`unexpected integration repair status: ${payload.status}`);
  }

  if (payload.command !== `GET ${INTEGRATION_REPAIR_PATH}`) {
    throw new Error(`unexpected integration repair command: ${payload.command}`);
  }

  if (payload.repairLevel !== "operator_repair_ready") {
    throw new Error(`unexpected integration repair level: ${payload.repairLevel}`);
  }

  if (payload.incidentCount !== 3 || payload.criticalCount !== 2 || payload.safeActionCount !== 1) {
    throw new Error("integration repair counts do not match the public contract");
  }

  for (const key of [
    "summary",
    "incidentMatrix",
    "repairRunbooks",
    "impactAnalysis",
    "repairActions",
    "safeExecutionPlan",
    "dataBoundaries",
  ]) {
    if (!Array.isArray(payload[key]) || payload[key].length === 0) {
      throw new Error(`integration repair ${key} is missing or empty`);
    }
  }

  const incidentIds = new Set(payload.incidentMatrix.map((item) => item?.incidentId));
  for (const incidentId of ["IR-001", "IR-002", "IR-003"]) {
    if (!incidentIds.has(incidentId)) {
      throw new Error(`integration repair incident is missing: ${incidentId}`);
    }
  }

  const runbookKeys = new Set(payload.repairRunbooks.map((item) => item?.runbookKey));
  for (const runbookKey of [
    "integration.retry_backlog",
    "integration.dead_letter",
    "integration.reconciliation_mismatch",
  ]) {
    if (!runbookKeys.has(runbookKey)) {
      throw new Error(`integration repair runbook is missing: ${runbookKey}`);
    }
  }

  const safeActions = payload.repairActions.filter((item) => item?.safeToAutoRun === true);
  if (safeActions.length !== 1 || safeActions[0]?.action !== "run_connection_diagnostics") {
    throw new Error("integration repair must expose exactly one safe diagnostic action");
  }

  if (payload.repairActions.some((item) => item?.providerCallEnabled !== false || item?.externalMutation !== false)) {
    throw new Error("integration repair actions must not call or mutate providers");
  }

  if (
    payload.dataBoundaries.some(
      (item) =>
        item?.containsPii !== false ||
        item?.rawPayloadIncluded !== false ||
        item?.providerCallEnabled !== false ||
        item?.externalMutation !== false,
    )
  ) {
    throw new Error("integration repair boundaries must stay public-safe");
  }
}

export function validateObservabilityDashboardPayload(payload) {
  const missing = OBSERVABILITY_DASHBOARD_REQUIRED_FIELDS.filter((field) => !(field in (payload || {})));
  if (missing.length > 0) {
    throw new Error(`missing observability dashboard fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "validated") {
    throw new Error(`unexpected observability dashboard status: ${payload.status}`);
  }

  if (payload.command !== `GET ${OBSERVABILITY_DASHBOARD_PATH}`) {
    throw new Error(`unexpected observability dashboard command: ${payload.command}`);
  }

  if (payload.dashboardLevel !== "dashboard_contract_ready") {
    throw new Error(`unexpected observability dashboard level: ${payload.dashboardLevel}`);
  }

  for (const key of ["summary", "dashboardGroups", "panelCatalog", "queryExamples", "alertLinks", "dataBoundaries"]) {
    if (!Array.isArray(payload[key]) || payload[key].length === 0) {
      throw new Error(`observability dashboard ${key} is missing or empty`);
    }
  }

  const groupKeys = new Set(payload.dashboardGroups.map((item) => item?.key));
  for (const groupKey of ["api_runtime", "integration_health", "business_workflow", "security_auth"]) {
    if (!groupKeys.has(groupKey)) {
      throw new Error(`observability dashboard group is missing: ${groupKey}`);
    }
  }

  const panelKeys = new Set(payload.panelCatalog.map((item) => item?.key));
  for (const panelKey of [
    "request_rate",
    "latency_p95",
    "error_ratio",
    "outbox_backlog",
    "dead_letters",
    "structured_logs",
  ]) {
    if (!panelKeys.has(panelKey)) {
      throw new Error(`observability dashboard panel is missing: ${panelKey}`);
    }
  }

  const datasources = new Set(payload.panelCatalog.map((item) => item?.datasource));
  for (const datasource of ["prometheus", "loki"]) {
    if (!datasources.has(datasource)) {
      throw new Error(`observability dashboard datasource is missing: ${datasource}`);
    }
  }

  const forbiddenLabels = new Set(["email", "user_id", "tenant_id", "token", "phone", "name", "payload", "request_body"]);
  for (const panel of payload.panelCatalog) {
    const labels = new Set(panel?.safeLabels || []);
    for (const label of labels) {
      if (forbiddenLabels.has(label)) {
        throw new Error(`unsafe observability dashboard label: ${label}`);
      }
    }
    if (!panel?.alertLink) {
      throw new Error(`observability dashboard panel missing alert link: ${panel?.key}`);
    }
  }

  if (
    payload.dataBoundaries.some(
      (item) =>
        item?.containsPii !== false ||
        item?.rawPayloadIncluded !== false ||
        item?.privateTelemetryIncluded !== false,
    )
  ) {
    throw new Error("observability dashboard boundaries must stay public-safe");
  }
}

export function validateBusinessScenarioReplayPayload(payload) {
  const missing = BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {
    throw new Error(`missing business scenario replay fields: ${missing.join(", ")}`);
  }

  if (payload.status !== "validated") {
    throw new Error(`unexpected business scenario replay status: ${payload.status}`);
  }

  if (payload.command !== "bash scripts/check_public_business_scenario_replay.sh") {
    throw new Error(`unexpected business scenario replay command: ${payload.command}`);
  }

  if (!Array.isArray(payload.scenarios) || payload.scenarios.length < 3) {
    throw new Error("business scenario replay scenarios are missing or too short");
  }

  const scenarioIds = new Set(payload.scenarios.map((item) => item?.id));
  for (const scenarioId of ["crm-bank-payment-mismatch", "support-sla-risk", "procurement-delay-risk"]) {
    if (!scenarioIds.has(scenarioId)) {
      throw new Error(`business scenario replay scenario is missing: ${scenarioId}`);
    }
  }

  for (const scenario of payload.scenarios) {
    if (!Array.isArray(scenario?.normalizedFacts) || scenario.normalizedFacts.length === 0) {
      throw new Error(`business scenario replay facts missing: ${scenario?.id}`);
    }
    if (!Array.isArray(scenario?.recommendedActions) || scenario.recommendedActions.length === 0) {
      throw new Error(`business scenario replay actions missing: ${scenario?.id}`);
    }
    if (!Array.isArray(scenario?.automationCandidates) || !scenario.automationCandidates.some((item) => item?.safeToAutoRun === false)) {
      throw new Error(`business scenario replay lacks approval boundary: ${scenario?.id}`);
    }
  }

  if (!Array.isArray(payload.flow) || payload.flow.length < 5) {
    throw new Error("business scenario replay flow is missing or too short");
  }

  if (!Array.isArray(payload.docs) || payload.docs.length < 4) {
    throw new Error("business scenario replay docs are missing or too short");
  }
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

  for (const key of ["summary", "flow", "operationPlans", "boundaries", "diagnostics", "docs"]) {
    if (!Array.isArray(payload.adapterStudio?.[key]) || payload.adapterStudio[key].length === 0) {
      throw new Error(`adapterStudio.${key} is missing or empty`);
    }
  }

  const adapterStudioPlans = new Map(payload.adapterStudio.operationPlans.map((item) => [item?.scenarioId, item]));
  for (const requiredPlan of ["adapter-crm-deal-preview", "adapter-crm-deal-ingest"]) {
    if (!adapterStudioPlans.has(requiredPlan)) {
      throw new Error(`adapterStudio.operationPlans does not include required plan: ${requiredPlan}`);
    }
  }

  if (adapterStudioPlans.get("adapter-crm-deal-preview")?.executionMode !== "contract_only") {
    throw new Error("adapterStudio CRM preview plan must be contract_only");
  }

  if (adapterStudioPlans.get("adapter-crm-deal-preview")?.safeToRunAgainstPublicDemo !== false) {
    throw new Error("adapterStudio CRM preview plan must not be marked safe for live public execution");
  }

  if (adapterStudioPlans.get("adapter-crm-deal-ingest")?.method !== "WORKER") {
    throw new Error("adapterStudio CRM ingest plan must be worker-backed");
  }

  const adapterStudioBoundaryEvidence = new Set(payload.adapterStudio.boundaries.map((item) => item?.evidence));
  for (const requiredEvidence of ["server_secret_store", "private_connector_only", "redaction_evidence"]) {
    if (!adapterStudioBoundaryEvidence.has(requiredEvidence)) {
      throw new Error(`adapterStudio.boundaries does not include required evidence: ${requiredEvidence}`);
    }
  }

  if (!payload.connectorFixtureReplay || typeof payload.connectorFixtureReplay !== "object") {
    throw new Error("connectorFixtureReplay is missing");
  }
  validateConnectorFixtureReplayPayload(payload.connectorFixtureReplay);

  if (!payload.connectorCertification || typeof payload.connectorCertification !== "object") {
    throw new Error("connectorCertification is missing");
  }
  validateConnectorCertificationPayload(payload.connectorCertification);

  if (!payload.providerOnboarding || typeof payload.providerOnboarding !== "object") {
    throw new Error("providerOnboarding is missing");
  }
  validateProviderOnboardingPayload(payload.providerOnboarding);

  if (!payload.integrationRepair || typeof payload.integrationRepair !== "object") {
    throw new Error("integrationRepair is missing");
  }
  validateIntegrationRepairPayload(payload.integrationRepair);

  if (!payload.observabilityDashboard || typeof payload.observabilityDashboard !== "object") {
    throw new Error("observabilityDashboard is missing");
  }
  validateObservabilityDashboardPayload(payload.observabilityDashboard);

  if (!payload.businessScenarioReplay || typeof payload.businessScenarioReplay !== "object") {
    throw new Error("businessScenarioReplay is missing");
  }
  validateBusinessScenarioReplayPayload(payload.businessScenarioReplay);

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
  const connectorReplay = await client.getConnectorFixtureReplay();
  const connectorCertification = await client.getConnectorCertification();
  const providerOnboarding = await client.getProviderOnboarding();
  const integrationRepair = await client.getIntegrationRepair();
  const observabilityDashboard = await client.getObservabilityDashboard();
  const businessScenarioReplay = await client.getBusinessScenarioReplay();
  const adapterPlan = buildAdapterOperationPlan(payload, "adapter-file-import-preview");
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${payload.workflow.currentStage}`,
    `adapterPlan=${adapterPlan.phase}`,
    `connectorReplay=${connectorReplay.status}`,
    `connectorCertification=${connectorCertification.certificationLevel}`,
    `providerOnboarding=${providerOnboarding.onboardingLevel}`,
    `integrationRepair=${integrationRepair.repairLevel}`,
    `observabilityDashboard=${observabilityDashboard.dashboardLevel}`,
    `businessScenarioReplay=${businessScenarioReplay.status}`,
    `operation=${OPERATION_ID}`,
    `connectorOperation=${CONNECTOR_REPLAY_OPERATION_ID}`,
    `connectorCertificationOperation=${CONNECTOR_CERTIFICATION_OPERATION_ID}`,
    `providerOnboardingOperation=${PROVIDER_ONBOARDING_OPERATION_ID}`,
    `integrationRepairOperation=${INTEGRATION_REPAIR_OPERATION_ID}`,
    `observabilityDashboardOperation=${OBSERVABILITY_DASHBOARD_OPERATION_ID}`,
    `businessScenarioOperation=${BUSINESS_SCENARIO_REPLAY_OPERATION_ID}`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
