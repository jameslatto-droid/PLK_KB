import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";

import { loadEnv } from "@/lib/server/env";

export type IngestJobStatus = "running" | "pass" | "fail";

export type IngestFileRecord = {
  path: string;
  documentId?: string;
  versionId?: string;
  artefactId?: string;
  chunkCount?: number;
};

export type IngestJob = {
  jobId: string;
  status: IngestJobStatus;
  startedAt: string;
  finishedAt?: string;
  currentStage?: string;
  events: Array<{
    ts: string;
    stage: string;
    message: string;
    status: "info" | "ok" | "warn" | "error";
    details?: string;
  }>;
  files: IngestFileRecord[];
  summary?: {
    artefacts: number;
    chunks: number;
    indexed_text?: number;
    indexed_vector?: number;
  };
  lastError?: string;
};

export type UserContextInput = {
  actor: string;
  roles: string[];
  classification: string;
};

const PYTHON = "/home/jim/PLK_KB/.venv/bin/python";
const ROOT = "/home/jim/PLK_KB";

const jobs = new Map<string, IngestJob>();
let activeJobId: string | null = null;

function nowIso(): string {
  return new Date().toISOString();
}

function pushEvent(job: IngestJob, event: Omit<IngestJob["events"][number], "ts">) {
  job.events.push({ ts: nowIso(), ...event });
}

function failJob(job: IngestJob, stage: string, error: string) {
  job.status = "fail";
  job.currentStage = stage;
  job.lastError = error;
  job.finishedAt = nowIso();
  pushEvent(job, { stage, status: "error", message: "FAILED", details: error });
}

function successJob(job: IngestJob) {
  job.status = "pass";
  job.currentStage = "complete";
  job.finishedAt = nowIso();
  pushEvent(job, { stage: "INGEST", status: "ok", message: "Ingestion complete" });
}

function withContextEnv(context: UserContextInput): NodeJS.ProcessEnv {
  loadEnv();
  return {
    ...process.env,
    PLK_ACTOR: context.actor,
    PLK_CONTEXT_ROLES: context.roles.join(","),
    PLK_CONTEXT_CLASSIFICATION: context.classification,
  };
}

function runCommand(args: string[], env: NodeJS.ProcessEnv, label: string): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, args, { cwd: ROOT, env });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });
    proc.on("error", (err) => reject(new Error(`${label} failed to start: ${err.message}`)));
    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`${label} exited with code ${code}: ${stderr.trim()}`));
        return;
      }
      resolve({ stdout: stdout.trim(), stderr: stderr.trim() });
    });
  });
}

function discoverFiles(rootPath: string): string[] {
  if (!fs.existsSync(rootPath)) {
    throw new Error(`Ingestion root missing: ${rootPath}`);
  }
  const entries = fs.readdirSync(rootPath);
  const files = entries
    .map((entry) => path.join(rootPath, entry))
    .filter((p) => fs.statSync(p).isFile() && p.toLowerCase().endsWith(".txt"));
  return files;
}

async function ingestFiles(job: IngestJob, env: NodeJS.ProcessEnv, files: string[]): Promise<void> {
  pushEvent(job, {
    stage: "INGESTION",
    status: "info",
    message: `Ingesting ${files.length} file(s)`,
    details: files.join(", "),
  });

  for (const [idx, filePath] of files.entries()) {
    const docId = `UI3-${job.jobId}-${String(idx + 1).padStart(3, "0")}`;
    const title = path.basename(filePath);
    const script = [
      "-c",
      [
        "import json, sys",
        "from pathlib import Path",
        "from modules.ingestion.app.cli import ingest_txt",
        "doc_id = sys.argv[1]",
        "title = sys.argv[2]",
        "fpath = Path(sys.argv[3])",
        "version_id, artefact_id = ingest_txt(",
        "    document_id=doc_id,",
        "    title=title,",
        "    path=fpath,",
        "    document_type='UI3_INGEST',",
        "    authority_level='REFERENCE'",
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
    job.files.push({ path: filePath, documentId: parsed.document_id, versionId: parsed.version_id, artefactId: parsed.artefact_id });
    pushEvent(job, {
      stage: "INGESTION",
      status: "ok",
      message: `Ingested ${title}`,
      details: `document_id=${parsed.document_id} artefact_id=${parsed.artefact_id}`,
    });
  }
}

async function chunkFiles(job: IngestJob, env: NodeJS.ProcessEnv): Promise<number> {
  pushEvent(job, { stage: "CHUNKING", status: "info", message: "Chunking artefacts" });
  let totalChunks = 0;
  for (const file of job.files) {
    if (!file.artefactId) continue;
    const result = await runCommand([
      "-m",
      "modules.chunking.app.pipeline",
      "--artefact-id",
      file.artefactId,
    ], env, `chunk ${file.artefactId}`);
    const match = result.stdout.match(/Chunks created: (\d+)/);
    const chunks = match ? Number(match[1]) : 0;
    file.chunkCount = chunks;
    totalChunks += chunks;
    pushEvent(job, {
      stage: "CHUNKING",
      status: "ok",
      message: `Chunked artefact ${file.artefactId}`,
      details: `chunks=${chunks}`,
    });
  }
  return totalChunks;
}

async function rebuildIndexes(job: IngestJob, env: NodeJS.ProcessEnv): Promise<{ text: number; vector: number }> {
  pushEvent(job, { stage: "INDEXING_TEXT", status: "info", message: "Rebuilding OpenSearch index" });
  const lex = await runCommand(["-m", "modules.indexing.app.indexer", "rebuild"], env, "index-lex");
  const lexMatch = lex.stdout.match(/Indexed chunks: (\d+)/);
  const textCount = lexMatch ? Number(lexMatch[1]) : 0;
  pushEvent(job, { stage: "INDEXING_TEXT", status: "ok", message: "OpenSearch index rebuilt", details: lex.stdout });

  pushEvent(job, { stage: "INDEXING_VECTOR", status: "info", message: "Rebuilding Qdrant vectors" });
  const vec = await runCommand(["-m", "modules.vector_indexing.app.indexer", "rebuild"], env, "index-vector");
  const vecMatch = vec.stdout.match(/Indexed chunks: (\d+)/);
  const vectorCount = vecMatch ? Number(vecMatch[1]) : 0;
  pushEvent(job, { stage: "INDEXING_VECTOR", status: "ok", message: "Qdrant vectors rebuilt", details: vec.stdout });

  return { text: textCount, vector: vectorCount };
}

async function executeIngest(job: IngestJob, rootPath: string, context: UserContextInput) {
  const env = withContextEnv(context);
  try {
    job.currentStage = "DISCOVERY";
    const files = discoverFiles(rootPath);
    if (files.length === 0) {
      throw new Error(`No .txt files found in ${rootPath}`);
    }
    pushEvent(job, { stage: "DISCOVERY", status: "ok", message: `Discovered ${files.length} file(s)` });

    job.currentStage = "INGESTION";
    await ingestFiles(job, env, files);

    job.currentStage = "CHUNKING";
    const chunks = await chunkFiles(job, env);

    job.currentStage = "INDEXING";
    const indexed = await rebuildIndexes(job, env);

    job.summary = {
      artefacts: job.files.length,
      chunks,
      indexed_text: indexed.text,
      indexed_vector: indexed.vector,
    };

    successJob(job);
  } catch (err) {
    failJob(job, job.currentStage ?? "INGEST", err instanceof Error ? err.message : String(err));
  } finally {
    activeJobId = null;
  }
}

export function startIngest(rootPath: string, context: UserContextInput): IngestJob {
  if (activeJobId) {
    const existing = jobs.get(activeJobId);
    if (existing) return existing;
  }

  const jobId = randomUUID();
  const job: IngestJob = {
    jobId,
    status: "running",
    startedAt: nowIso(),
    files: [],
    events: [],
  };
  jobs.set(jobId, job);
  activeJobId = jobId;
  pushEvent(job, { stage: "INGEST", status: "info", message: `Ingest job started at ${rootPath}` });
  setImmediate(() => executeIngest(job, rootPath, context));
  return job;
}

export function getIngest(jobId: string): IngestJob | null {
  return jobs.get(jobId) ?? null;
}
