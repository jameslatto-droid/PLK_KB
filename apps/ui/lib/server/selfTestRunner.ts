import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";

import { loadEnv } from "@/lib/server/env";

export type SelfTestStatus = "running" | "pass" | "fail";
export type SelfTestEventStatus = "info" | "ok" | "warn" | "error";

export type SelfTestEvent = {
  ts: string;
  stage: string;
  message: string;
  status: SelfTestEventStatus;
  details?: string;
};

export type SelfTestRun = {
  runId: string;
  status: SelfTestStatus;
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

const FIXTURE_PATH = "/home/jim/PLK_KB/ops/scripts/stage5_tmp";
const PYTHON = "/home/jim/PLK_KB/.venv/bin/python";
const ROOT = "/home/jim/PLK_KB";

const runs = new Map<string, SelfTestRun>();
let activeRunId: string | null = null;

export type UserContextInput = {
  actor: string;
  roles: string[];
  classification: string;
};

function nowIso(): string {
  return new Date().toISOString();
}

function pushEvent(run: SelfTestRun, event: Omit<SelfTestEvent, "ts">) {
  run.events.push({ ts: nowIso(), ...event });
}

function failRun(run: SelfTestRun, stage: string, error: string) {
  run.status = "fail";
  run.currentStage = stage;
  run.lastError = error;
  run.finishedAt = nowIso();
  pushEvent(run, { stage, status: "error", message: "FAILED", details: error });
}

function successRun(run: SelfTestRun) {
  run.status = "pass";
  run.finishedAt = nowIso();
  run.currentStage = "complete";
  pushEvent(run, { stage: "SELF_TEST", status: "ok", message: "PASS", details: "All stages completed." });
}

function withContextEnv(context?: UserContextInput): NodeJS.ProcessEnv {
  loadEnv();
  const actor = context?.actor ?? "jim";
  const roles = context?.roles?.length ? context.roles : ["SUPERUSER"];
  const classification = context?.classification ?? "REFERENCE";
  return {
    ...process.env,
    PLK_ACTOR: actor,
    PLK_CONTEXT_ROLES: roles.join(","),
    PLK_CONTEXT_CLASSIFICATION: classification,
  };
}

function runCommand(
  args: string[],
  env: NodeJS.ProcessEnv,
  label: string
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, args, {
      cwd: ROOT,
      env,
    });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("error", (err) => {
      reject(new Error(`${label} failed to start: ${err.message}`));
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`${label} exited with code ${code}. stderr: ${stderr.trim()}`));
        return;
      }
      resolve({ stdout: stdout.trim(), stderr: stderr.trim() });
    });
  });
}

function requireFixtureFiles(): string[] {
  if (!fs.existsSync(FIXTURE_PATH)) {
    throw new Error(`Fixture path missing: ${FIXTURE_PATH}`);
  }
  const entries = fs.readdirSync(FIXTURE_PATH);
  const files = entries
    .map((entry) => path.join(FIXTURE_PATH, entry))
    .filter((file) => file.endsWith(".txt"));
  if (files.length === 0) {
    throw new Error(`No .txt fixtures found in ${FIXTURE_PATH}`);
  }
  return files;
}

async function ingestFixture(run: SelfTestRun, env: NodeJS.ProcessEnv): Promise<void> {
  const files = requireFixtureFiles();
  pushEvent(run, {
    stage: "INGESTION",
    status: "info",
    message: `Ingesting ${files.length} fixture files`,
    details: FIXTURE_PATH,
  });

  for (const [index, filePath] of files.entries()) {
    const docId = `UI2-${run.runId}-${String(index + 1).padStart(3, "0")}`;
    const title = path.basename(filePath);
    const script = [
      "-c",
      [
        "import json, sys",
        "from pathlib import Path",
        "from modules.ingestion.app.cli import ingest_txt",
        "doc_id = sys.argv[1]",
        "title = sys.argv[2]",
        "path = Path(sys.argv[3])",
        "version_id, artefact_id = ingest_txt(",
        "    document_id=doc_id,",
        "    title=title,",
        "    path=path,",
        "    document_type='SELF_TEST',",
        "    authority_level='AUTHORITATIVE'",
        ")",
        "print(json.dumps({",
        "    'document_id': doc_id,",
        "    'version_id': version_id,",
        "    'artefact_id': artefact_id",
        "}))",
      ].join("\n"),
      docId,
      title,
      filePath,
    ];
    const result = await runCommand(script, env, `ingest ${title}`);
    const parsed = JSON.parse(result.stdout || "{}");
    run.artefacts.push({
      documentId: parsed.document_id,
      versionId: parsed.version_id,
      artefactId: parsed.artefact_id,
      path: filePath,
    });
    pushEvent(run, {
      stage: "INGESTION",
      status: "ok",
      message: `Ingested ${title}`,
      details: `document_id=${parsed.document_id} artefact_id=${parsed.artefact_id}`,
    });
  }
}

async function chunkArtefacts(run: SelfTestRun, env: NodeJS.ProcessEnv): Promise<void> {
  pushEvent(run, {
    stage: "CHUNKING",
    status: "info",
    message: `Chunking ${run.artefacts.length} artefacts`,
  });
  for (const artefact of run.artefacts) {
    const result = await runCommand(
      ["-m", "modules.chunking.app.pipeline", "--artefact-id", artefact.artefactId],
      env,
      `chunk ${artefact.artefactId}`
    );
    pushEvent(run, {
      stage: "CHUNKING",
      status: "ok",
      message: `Chunked artefact ${artefact.artefactId}`,
      details: result.stdout || undefined,
    });
  }
}

async function rebuildIndexes(run: SelfTestRun, env: NodeJS.ProcessEnv): Promise<void> {
  pushEvent(run, { stage: "INDEXING_TEXT", status: "info", message: "Rebuilding OpenSearch index" });
  const lexResult = await runCommand(["-m", "modules.indexing.app.indexer", "rebuild"], env, "index-lex");
  pushEvent(run, {
    stage: "INDEXING_TEXT",
    status: "ok",
    message: "OpenSearch index rebuilt",
    details: lexResult.stdout || undefined,
  });

  pushEvent(run, { stage: "INDEXING_VECTOR", status: "info", message: "Rebuilding Qdrant vectors" });
  const vecResult = await runCommand(
    ["-m", "modules.vector_indexing.app.indexer", "rebuild"],
    env,
    "index-vector"
  );
  pushEvent(run, {
    stage: "INDEXING_VECTOR",
    status: "ok",
    message: "Qdrant vectors rebuilt",
    details: vecResult.stdout || undefined,
  });
}

async function runSearch(run: SelfTestRun, env: NodeJS.ProcessEnv): Promise<void> {
  const query = "deployment test";
  pushEvent(run, { stage: "SEARCH", status: "info", message: `Running query: ${query}` });
  const script = [
    "-c",
    [
      "import json",
      "from modules.hybrid_search.app.search import hybrid_search",
      "from modules.metadata.app.db import connection_cursor",
      "response = hybrid_search('deployment test', top_k=5)",
      "query_id = response.get('query_id')",
      "outcome = {'evaluated': 0, 'denied': 0, 'allowed': 0}",
      "with connection_cursor(dict_cursor=True) as cur:",
      "    cur.execute(\"\"\"",
      "        SELECT details FROM audit_log",
      "        WHERE action='AUTHORITY_EVALUATED' AND details->>'query_id' = %s",
      "        ORDER BY audit_id DESC LIMIT 1",
      "    \"\"\", (query_id,))",
      "    row = cur.fetchone()",
      "    if row and row.get('details') and row['details'].get('outcome'):",
      "        outcome = row['details']['outcome']",
      "print(json.dumps({'response': response, 'authority_summary': outcome}))",
    ].join("\n"),
  ];
  const result = await runCommand(script, env, "search");
  const parsed = JSON.parse(result.stdout || "{}");
  const response = parsed.response ?? { results: [] };
  const summary = parsed.authority_summary ?? { evaluated: 0, denied: 0, allowed: 0 };

  run.searchSummary = {
    query,
    queryId: response.query_id ?? "",
    resultCount: Array.isArray(response.results) ? response.results.length : 0,
    deniedCount: Number(summary.denied ?? 0),
  };

  pushEvent(run, {
    stage: "AUTHORITY",
    status: "ok",
    message: `Authority evaluated: allowed=${summary.allowed ?? 0} denied=${summary.denied ?? 0}`,
  });
  pushEvent(run, {
    stage: "RESPONSE",
    status: "ok",
    message: `Search returned ${run.searchSummary.resultCount} results`,
    details: `query_id=${run.searchSummary.queryId}`,
  });
}

async function executeSelfTest(run: SelfTestRun, context?: UserContextInput): Promise<void> {
  const env = withContextEnv(context);
  try {
    run.currentStage = "BOOTSTRAP";
    pushEvent(run, { stage: "BOOTSTRAP", status: "info", message: "Bootstrapping metadata schema" });
    await runCommand(["-m", "modules.metadata.app.bootstrap"], env, "bootstrap");
    pushEvent(run, { stage: "BOOTSTRAP", status: "ok", message: "Metadata schema ready" });

    run.currentStage = "INGESTION";
    await ingestFixture(run, env);

    run.currentStage = "CHUNKING";
    await chunkArtefacts(run, env);

    run.currentStage = "INDEXING";
    await rebuildIndexes(run, env);

    run.currentStage = "SEARCH";
    await runSearch(run, env);

    successRun(run);
  } catch (err) {
    failRun(run, run.currentStage ?? "SELF_TEST", err instanceof Error ? err.message : String(err));
  } finally {
    activeRunId = null;
  }
}

export function startSelfTest(context?: UserContextInput): SelfTestRun {
  if (activeRunId) {
    const existing = runs.get(activeRunId);
    if (existing) {
      return existing;
    }
  }

  const runId = randomUUID();
  const run: SelfTestRun = {
    runId,
    status: "running",
    startedAt: nowIso(),
    events: [],
    artefacts: [],
  };
  runs.set(runId, run);
  activeRunId = runId;
  pushEvent(run, { stage: "SELF_TEST", status: "info", message: "Self-test started" });
  setImmediate(() => executeSelfTest(run, context));
  return run;
}

export function getSelfTest(runId: string): SelfTestRun | null {
  return runs.get(runId) ?? null;
}
