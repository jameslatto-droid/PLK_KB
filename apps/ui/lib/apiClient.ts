type ApiOptions = {
  baseUrl?: string;
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
