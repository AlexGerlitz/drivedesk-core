// Generated from DriveDesk Core OpenAPI. Do not edit by hand.
export const PUBLIC_DEMO_PATH: "/demo/public";
export const OPERATION_ID: "public_demo_demo_public_get";
export const REQUIRED_FIELDS: Array<"schemaVersion" | "generatedAt" | "dataSource" | "apiContract" | "tenant" | "health" | "metrics" | "workQueue" | "members" | "auditEvents" | "outbox" | "adapters" | "integrationJobs" | "integrationHealth" | "integrationReadiness" | "workflow" | "timeline" | "domainEvents">;

export interface PublicDemoPayload {
  schemaVersion: 1;
  generatedAt: string;
  dataSource: "api.synthetic";
  apiContract: Record<string, string>;
  tenant: Record<string, string>;
  health: Record<string, string>;
  metrics: Array<Record<string, unknown>>;
  workQueue: Array<Record<string, unknown>>;
  members: Array<Record<string, string>>;
  auditEvents: Array<Record<string, string>>;
  outbox: Array<Record<string, unknown>>;
  adapters: Array<Record<string, string>>;
  integrationJobs: Array<Record<string, unknown>>;
  integrationHealth: Array<Record<string, string>>;
  integrationReadiness: Array<Record<string, unknown>>;
  workflow: {
    id: "wf-demo-lead-to-student";
    currentStage: "student_sync";
    stages: Array<Record<string, string>>;
    [key: string]: unknown;
  };
  timeline: Array<Record<string, string>>;
  domainEvents: Array<Record<string, string>>;
}

export class DriveDeskPublicDemoClient {
  constructor(baseUrl?: string, options?: { fetchImpl?: typeof fetch });
  getPublicDemo(): Promise<PublicDemoPayload>;
}

export function validatePublicDemoPayload(payload: PublicDemoPayload): void;
