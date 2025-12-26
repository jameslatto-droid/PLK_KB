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

const DEFAULT_ROOT = path.resolve(process.cwd(), "..", "..");
const ROOT = process.env.PLK_ROOT || DEFAULT_ROOT;
const PYTHON = process.env.PLK_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const MAX_OUTPUT_BYTES = 500_000;
const DEFAULT_TIMEOUT_MS = 30_000; // non-ingest commands remain at 30s
const INGEST_TIMEOUT_MS = (Number(process.env.PLK_INGEST_TIMEOUT_SECONDS) || 600) * 1000; // ingestion can take longer

const jobs = new Map<string, IngestJob>();
let activeJobId: string | null = null;
// Supported text-like formats; binary/structured formats (PDF/DOCX/OCR/CAD) remain deferred.
const ALLOWED_INGEST_EXTENSIONS = [".txt", ".md", ".csv", ".log", ".json", ".rtf"];
// Enable verbose ingest logging by default; set PLK_INGEST_DEBUG=0 to silence.
const INGEST_DEBUG = process.env.PLK_INGEST_DEBUG !== "0";

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
  const envVars = loadEnv(); // Load and return all env vars including ops/docker/.env
  return {
    ...process.env,
    ...envVars, // Explicitly include loaded env vars (POSTGRES_*, OPENSEARCH_*, MINIO_*, QDRANT_*)
    PLK_ACTOR: context.actor,
    PLK_CONTEXT_ROLES: context.roles.join(","),
    PLK_CONTEXT_CLASSIFICATION: context.classification,
  };
}

function runCommand(
  args: string[],
  env: NodeJS.ProcessEnv,
  label: string,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, args, { cwd: ROOT, env });
    let stdout = "";
    let stderr = "";
    const start = Date.now();
    const timer = setTimeout(() => {
      proc.kill("SIGKILL");
      const elapsed = Date.now() - start;
      reject(new Error(`${label} timed out after ${elapsed}ms (timeout=${timeoutMs}ms)`));
    }, timeoutMs);

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
      if (INGEST_DEBUG) {
        console.log(`[ingest-debug][stdout][${label}] ${data.toString().trimEnd()}`);
      }
      if (stdout.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error(`${label} output exceeded limit`));
      }
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
      if (INGEST_DEBUG) {
        console.error(`[ingest-debug][stderr][${label}] ${data.toString().trimEnd()}`);
      }
      if (stderr.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error(`${label} error output exceeded limit`));
      }
    });
    proc.on("error", (err) => {
      clearTimeout(timer);
      reject(new Error(`${label} failed to start: ${err.message}`));
    });
    proc.on("close", (code) => {
      clearTimeout(timer);
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
  const allowed = new Set(ALLOWED_INGEST_EXTENSIONS.map((e) => e.toLowerCase()));

  let scanned = 0;
  let skipped = 0;
  const files: string[] = [];

  const walk = (dir: string) => {
    const entries = fs.readdirSync(dir);
    for (const entry of entries) {
      const full = path.join(dir, entry);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) {
        walk(full);
        continue;
      }
      scanned += 1;
      const ext = path.extname(full).toLowerCase();
      const ok = allowed.has(ext);
      if (ok) {
        files.push(full);
      } else {
        skipped += 1;
      }
    }
  };

  walk(rootPath);

  console.log(
    `[ingest] Scanning ${rootPath} | scanned=${scanned} accepted=${files.length} skipped=${skipped} allowed=${Array.from(allowed).join(
      ", "
    )}`
  );

  if (files.length === 0) {
    throw new Error(
      `No ingestable files found in ${rootPath}. Allowed file types: ${Array.from(allowed).join(", ")}`
    );
  }

  return files;
}

function describeDir(dirPath: string): string | null {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true }).slice(0, 15);
    if (!entries.length) return "(empty)";
    return entries.map((e) => `${e.name}${e.isDirectory() ? "/" : ""}`).join(", ");
  } catch (err) {
    return null;
  }
}

async function ingestFiles(job: IngestJob, env: NodeJS.ProcessEnv, files: string[], rootPath: string): Promise<void> {
  pushEvent(job, {
    stage: "INGESTION",
    status: "info",
    message: `Ingesting ${files.length} file(s)`,
    details: files.join(", "),
  });

  for (const [idx, filePath] of files.entries()) {
    if (!fs.existsSync(filePath)) {
      const dir = path.dirname(filePath);
      const listingDir = fs.existsSync(dir) ? dir : rootPath;
      const listing = describeDir(listingDir);
      const hint = listing ? ` Directory listing (${listingDir}): ${listing}` : "";
      throw new Error(`File not found: ${filePath}. Check mounts/volume mappings.${hint}`);
    }

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
    const result = await runCommand(script, env, `INGESTION: ${title}`, INGEST_TIMEOUT_MS);
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
    ], env, `CHUNKING: ${file.artefactId}`, INGEST_TIMEOUT_MS);
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
  const lex = await runCommand(["-m", "modules.indexing.app.indexer", "rebuild"], env, "INDEXING_TEXT: rebuild", INGEST_TIMEOUT_MS);
  const lexMatch = lex.stdout.match(/Indexed chunks: (\d+)/);
  const textCount = lexMatch ? Number(lexMatch[1]) : 0;
  pushEvent(job, { stage: "INDEXING_TEXT", status: "ok", message: "OpenSearch index rebuilt", details: lex.stdout });

  pushEvent(job, { stage: "INDEXING_VECTOR", status: "info", message: "Rebuilding Qdrant vectors" });
  const vec = await runCommand(["-m", "modules.vector_indexing.app.indexer", "rebuild"], env, "INDEXING_VECTOR: rebuild", INGEST_TIMEOUT_MS);
  const vecMatch = vec.stdout.match(/Indexed chunks: (\d+)/);
  const vectorCount = vecMatch ? Number(vecMatch[1]) : 0;
  pushEvent(job, { stage: "INDEXING_VECTOR", status: "ok", message: "Qdrant vectors rebuilt", details: vec.stdout });

  return { text: textCount, vector: vectorCount };
}

async function executeIngest(job: IngestJob, rootPath: string, context: UserContextInput) {
  const env = withContextEnv(context);
  const phaseLog = (phase: string, message: string) => {
    console.log(`[ingest] ${phase} | ${message}`);
  };
  try {
    job.currentStage = "DISCOVERY";
    const files = discoverFiles(rootPath);
    pushEvent(job, { stage: "DISCOVERY", status: "ok", message: `Discovered ${files.length} file(s)` });

    job.currentStage = "INGESTION";
    const tIngestStart = Date.now();
    phaseLog("INGESTION", `starting (${files.length} file(s))`);
    await ingestFiles(job, env, files, rootPath);
    phaseLog("INGESTION", `done in ${Date.now() - tIngestStart}ms`);

    job.currentStage = "CHUNKING";
    const tChunkStart = Date.now();
    phaseLog("CHUNKING", "starting");
    const chunks = await chunkFiles(job, env);
    phaseLog("CHUNKING", `done in ${Date.now() - tChunkStart}ms`);

    job.currentStage = "INDEXING";
    const tIndexStart = Date.now();
    phaseLog("INDEXING", "starting");
    const indexed = await rebuildIndexes(job, env);
    phaseLog("INDEXING", `done in ${Date.now() - tIndexStart}ms`);

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
