"use client";

import { useEffect, useState } from "react";
import { fetchIngest, startIngest, type IngestJob } from "@/lib/apiClient";
import { usePipelineLog } from "@/components/PipelineLogContext";
import { useUserContext } from "@/components/UserContext";
import StageStepper from "@/components/StageStepper";

const POLL_MS = 2000;
const DEFAULT_ROOT = process.env.NEXT_PUBLIC_PLK_INGESTION_ROOT || "/home/jim/PLK_KB/data/testdata";

// Map job stage to stepper step
function mapStageToStep(stage?: string): "ingestion" | "chunking" | "indexing-text" | "indexing-vector" | "search" | "authority" | "response" {
  if (!stage) return "ingestion";
  const lower = stage.toLowerCase();
  if (lower.includes("chunk")) return "chunking";
  if (lower.includes("index")) return "indexing-text"; // Default to text indexing stage
  return "ingestion";
}

export default function IngestionPanel() {
  const [rootPath, setRootPath] = useState(DEFAULT_ROOT);
  const [job, setJob] = useState<IngestJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const { setEvents } = usePipelineLog();
  const { active } = useUserContext();

  useEffect(() => {
    if (!job) return;
    setEvents(job.events ?? []);
  }, [job, setEvents]);

  useEffect(() => {
    if (!job || job.status !== "running") return;
    let activePoll = true;
    const poll = async () => {
      try {
        const updated = await fetchIngest(job.jobId);
        if (!activePoll) return;
        setJob(updated);
        setError(null);
      } catch (err) {
        if (!activePoll) return;
        setError(err instanceof Error ? err.message : "ingest polling failed");
      }
    };
    const timer = setInterval(poll, POLL_MS);
    return () => {
      activePoll = false;
      clearInterval(timer);
    };
  }, [job]);

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      const started = await startIngest(rootPath, {
        actor: active.actor,
        roles: active.roles,
        classification: active.classification,
      });
      setJob(started);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ingest start failed");
    } finally {
      setStarting(false);
    }
  };

  return (
    <>
      <StageStepper currentStep={mapStageToStep(job?.currentStage)} />
      
      <section className="panel">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="panel-heading">Ingestion Runner</p>
            <h3 className="mt-2 text-lg font-semibold text-ink-900">Register + Chunk + Index</h3>
            <p className="mt-1 text-sm text-ink-600">Dev-only convenience. Calls Python CLIs (ingest → chunk → index) with full audit and authority context.</p>
            <p className="mt-1 text-xs text-ink-500">Actor: {active.actor} · Roles: {active.roles.join(", ")} · Classification: {active.classification}</p>
          </div>
          <button
          type="button"
          className="rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white"
          onClick={start}
          disabled={starting || job?.status === "running"}
        >
          {starting || job?.status === "running" ? "Running..." : "Ingest Folder"}
        </button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm text-ink-700">
          Ingestion root (mounted):
          <input
            className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
            value={rootPath}
            onChange={(e) => setRootPath(e.target.value)}
            placeholder={DEFAULT_ROOT}
          />
          <span className="text-xs text-ink-500">Expected Windows path: D:\\TestData → mounted as /mnt/d/TestData</span>
        </label>
        <div className="rounded-xl border border-ink-100 bg-ink-50/60 p-3 text-xs text-ink-600">
          <p className="font-semibold text-ink-700">What happens</p>
          <ol className="list-decimal pl-4">
            <li>Discover text files (.txt, .md, .csv, .log, .json, .rtf) under the root (recursive)</li>
            <li>Ingest via modules.ingestion.app.cli (MinIO + Postgres)</li>
            <li>Chunk each artefact</li>
            <li>Rebuild OpenSearch + Qdrant indexes</li>
          </ol>
        </div>
      </div>

      {error ? (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Job ID</p>
          <p className="mt-2 text-sm text-ink-700">{job?.jobId ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Status</p>
          <p className="mt-2 text-sm font-semibold text-ink-900">{job?.status ?? "IDLE"}</p>
          {job?.lastError ? <p className="mt-1 text-xs text-rose-600">{job.lastError}</p> : null}
        </div>
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Summary</p>
          <p className="mt-2 text-sm text-ink-700">
            Artefacts: {job?.summary?.artefacts ?? 0} · Chunks: {job?.summary?.chunks ?? 0}
          </p>
          <p className="mt-1 text-xs text-ink-500">Index text: {job?.summary?.indexed_text ?? 0} · vector: {job?.summary?.indexed_vector ?? 0}</p>
        </div>
      </div>

      <div className="mt-4">
        <p className="panel-heading">Files</p>
        {job?.files?.length ? (
          <div className="mt-2 divide-y divide-ink-100 rounded-xl border border-ink-100 bg-white/70">
            {job.files.map((file) => (
              <div key={file.path} className="flex flex-col gap-1 px-3 py-2 text-sm text-ink-700">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold">{file.path}</span>
                  <span className="pill">artefact: {file.artefactId ?? "—"}</span>
                </div>
                <div className="flex flex-wrap gap-2 text-xs text-ink-500">
                  <span className="pill">doc: {file.documentId ?? "pending"}</span>
                  <span className="pill">version: {file.versionId ?? "pending"}</span>
                  <span className="pill">chunks: {file.chunkCount ?? 0}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-ink-500">No files ingested yet.</p>
        )}
      </div>
    </section>
    </>
  );
}
