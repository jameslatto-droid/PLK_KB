export type PipelineEventStatus = "info" | "ok" | "warn" | "error";

export type PipelineEvent = {
  ts: string;
  stage: string;
  message: string;
  status: PipelineEventStatus;
  details?: string;
};

export type PipelinePageKey = "dashboard" | "ingest" | "artefacts" | "search" | "self-test" | "audit";

export const pipelineEventsByPage: Record<PipelinePageKey, PipelineEvent[]> = {
  dashboard: [
    {
      ts: "2024-12-26T12:00:00Z",
      stage: "SYSTEM",
      message: "Pipeline online, awaiting operator input.",
      status: "info",
      details: "All services reachable. No ingestion or search jobs active.",
    },
    {
      ts: "2024-12-26T12:05:22Z",
      stage: "AUTHORITY",
      message: "Deny-by-default enforced for unauthenticated context.",
      status: "ok",
      details: "No access rules matched. Responses withheld as expected.",
    },
  ],
  ingest: [
    {
      ts: "2024-12-26T12:10:01Z",
      stage: "INGESTION",
      message: "Scanning artefact directory: /mnt/d/TestData",
      status: "info",
    },
    {
      ts: "2024-12-26T12:10:20Z",
      stage: "METADATA",
      message: "Artefact registry updated (3 artefacts).",
      status: "ok",
      details: "artefact_ids: 3 generated. version_id: v1",
    },
  ],
  artefacts: [
    {
      ts: "2024-12-26T12:14:05Z",
      stage: "METADATA",
      message: "Artefact inventory loaded.",
      status: "ok",
      details: "39 artefacts indexed, 5 awaiting chunking.",
    },
    {
      ts: "2024-12-26T12:14:20Z",
      stage: "VALIDATION",
      message: "Access rules attached to 12 artefacts.",
      status: "warn",
      details: "27 artefacts have no access rules and remain denied by default.",
    },
  ],
  search: [
    {
      ts: "2024-12-26T12:20:00Z",
      stage: "SEARCH",
      message: "Hybrid retrieval executed for query: deployment test",
      status: "ok",
      details: "lexical: 12 hits, semantic: 8 hits, merged: 10 candidates",
    },
    {
      ts: "2024-12-26T12:20:02Z",
      stage: "AUTHORITY",
      message: "Authority filter applied to candidate set.",
      status: "ok",
      details: "7 allowed, 3 denied. Reasons recorded in audit log.",
    },
    {
      ts: "2024-12-26T12:20:04Z",
      stage: "RESPONSE",
      message: "Explainable response constructed.",
      status: "ok",
      details: "All results include match, allow, and rank explanations.",
    },
  ],
  "self-test": [
    {
      ts: "2024-12-26T12:30:10Z",
      stage: "SELF-TEST",
      message: "Pipeline smoke test started.",
      status: "info",
    },
    {
      ts: "2024-12-26T12:30:20Z",
      stage: "SELF-TEST",
      message: "PASS: ingestion + indexing completed.",
      status: "ok",
      details: "OpenSearch and Qdrant counts verified > 0.",
    },
    {
      ts: "2024-12-26T12:30:24Z",
      stage: "SELF-TEST",
      message: "FAIL (sample): audit logging unavailable.",
      status: "error",
      details: "This is a mocked failure example to demonstrate explainable diagnostics.",
    },
  ],
  audit: [
    {
      ts: "2024-12-26T12:35:12Z",
      stage: "AUDIT",
      message: "Decision log queried for last 24 hours.",
      status: "info",
    },
    {
      ts: "2024-12-26T12:35:18Z",
      stage: "AUTHORITY",
      message: "ALLOW decision recorded with rule_id=RULE_SUPERUSER_ALL.",
      status: "ok",
      details: "document_id=doc_482, reason=ROLE_MATCH",
    },
    {
      ts: "2024-12-26T12:35:20Z",
      stage: "AUTHORITY",
      message: "DENY decision recorded (no access rules).",
      status: "warn",
      details: "document_id=doc_488, reason=NO_ACCESS_RULES",
    },
  ],
};
