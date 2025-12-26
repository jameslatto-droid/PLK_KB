type ApiOptions = {
  baseUrl?: string;
};

export type UserContextPayload = {
  actor: string;
  roles: string[];
  classification: string;
};

export type PipelineEvent = {
  ts: string;
  stage: string;
  message: string;
  status: "info" | "ok" | "warn" | "error";
  details?: string;
};

export type BackendStatusResponse = {
  timestamp: string;
  services: {
    postgres: { reachable: boolean; detail?: string };
    opensearch: { reachable: boolean; detail?: string; indices?: string[]; indexCount?: number };
    qdrant: { reachable: boolean; detail?: string; collections?: string[]; pointsCount?: number };
    minio: { reachable: boolean; detail?: string };
  };
};

export type SelfTestEvent = {
  ts: string;
  stage: string;
  message: string;
  status: "info" | "ok" | "warn" | "error";
  details?: string;
};

export type SelfTestRun = {
  runId: string;
  status: "running" | "pass" | "fail";
  startedAt: string;
  finishedAt?: string;
  currentStage?: string;
  events: SelfTestEvent[];
  artefacts: {
    documentId: string;
    versionId: string;
    artefactId: string;
    path: string;
  }[];
  lastError?: string;
  searchSummary?: {
    query: string;
    queryId: string;
    resultCount: number;
    deniedCount: number;
  };
};

export type SearchResult = {
  document_id: string;
  chunk_id: string;
  snippet: string;
  scores: { lexical: number; semantic: number; final: number };
  authority: { decision: "ALLOW"; matched_rule_ids: number[] };
  explanation: { why_matched: string; why_allowed: string; why_ranked: string };
};

export type SearchResponse = {
  response: {
    query_id: string;
    timestamp: string;
    query: string;
    results: SearchResult[];
  };
  authority_summary: { evaluated?: number; denied?: number; allowed?: number };
};

export type AccessRuleRecord = {
  rule_id: number;
  document_id: string;
  title: string;
  classification: string | null;
  allowed_roles: string[];
  project_code: string | null;
  discipline: string | null;
  commercial_sensitivity: string | null;
  created_at: string;
};

export type SeedAccessResult = {
  seeded_superuser: number;
  seeded_user: number;
  documents_seen: number;
};

export type IngestJob = {
  jobId: string;
  status: "running" | "pass" | "fail";
  startedAt: string;
  finishedAt?: string;
  currentStage?: string;
  events: PipelineEvent[];
  files: Array<{
    path: string;
    documentId?: string;
    versionId?: string;
    artefactId?: string;
    chunkCount?: number;
  }>;
  summary?: {
    artefacts: number;
    chunks: number;
    indexed_text?: number;
    indexed_vector?: number;
  };
  lastError?: string;
};

export type ArtefactRecord = {
  artefact_id: string;
  version_id: string;
  artefact_type: string;
  storage_path: string;
  created_at: string;
  document_id: string;
  version_label: string;
  title: string;
  document_type: string;
  authority_level: string;
  project_code: string | null;
  chunk_count: number;
};

export type ArtefactDetail = ArtefactRecord & {
  opensearch_count?: number;
  qdrant_count?: number;
  last_indexed_at?: string | null;
  opensearch_error?: string;
  qdrant_error?: string;
};

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchBackendStatus(options: ApiOptions = {}): Promise<BackendStatusResponse> {
  const base = options.baseUrl ?? "";
  return fetchJson<BackendStatusResponse>(`${base}/api/status`);
}

export async function startSelfTest(options: ApiOptions = {}): Promise<SelfTestRun> {
  const base = options.baseUrl ?? "";
  return fetchJson<SelfTestRun>(`${base}/api/self-test`, { method: "POST" });
}

export async function fetchSelfTest(runId: string, options: ApiOptions = {}): Promise<SelfTestRun> {
  const base = options.baseUrl ?? "";
  return fetchJson<SelfTestRun>(`${base}/api/self-test?run_id=${encodeURIComponent(runId)}`);
}

export async function runSearch(query: string, options: ApiOptions = {}): Promise<SearchResponse> {
  const base = options.baseUrl ?? "";
  return fetchJson<SearchResponse>(`${base}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
}

export async function runSearchWithContext(
  query: string,
  context: UserContextPayload,
  options: ApiOptions = {}
): Promise<SearchResponse> {
  const base = options.baseUrl ?? "";
  return fetchJson<SearchResponse>(`${base}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, context }),
  });
}

export async function fetchAccessRules(options: ApiOptions = {}): Promise<AccessRuleRecord[]> {
  const base = options.baseUrl ?? "";
  return fetchJson<AccessRuleRecord[]>(`${base}/api/access`);
}

export async function seedAccessRules(
  context: UserContextPayload,
  options: ApiOptions = {}
): Promise<SeedAccessResult> {
  const base = options.baseUrl ?? "";
  return fetchJson<SeedAccessResult>(`${base}/api/access/seed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
}

export async function startIngest(
  rootPath: string,
  context: UserContextPayload,
  options: ApiOptions = {}
): Promise<IngestJob> {
  const base = options.baseUrl ?? "";
  return fetchJson<IngestJob>(`${base}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rootPath, context }),
  });
}

export async function fetchIngest(jobId: string, options: ApiOptions = {}): Promise<IngestJob> {
  const base = options.baseUrl ?? "";
  return fetchJson<IngestJob>(`${base}/api/ingest?job_id=${encodeURIComponent(jobId)}`);
}

export async function listArtefacts(options: ApiOptions = {}): Promise<ArtefactRecord[]> {
  const base = options.baseUrl ?? "";
  return fetchJson<ArtefactRecord[]>(`${base}/api/artefacts`);
}

export async function getArtefactDetail(
  artefactId: string,
  options: ApiOptions = {}
): Promise<ArtefactDetail> {
  const base = options.baseUrl ?? "";
  return fetchJson<ArtefactDetail>(`${base}/api/artefacts/${encodeURIComponent(artefactId)}`);
}

export async function startSelfTestWithContext(
  context: UserContextPayload,
  options: ApiOptions = {}
): Promise<SelfTestRun> {
  const base = options.baseUrl ?? "";
  return fetchJson<SelfTestRun>(`${base}/api/self-test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
}
