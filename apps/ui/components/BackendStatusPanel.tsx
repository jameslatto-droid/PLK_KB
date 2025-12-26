"use client";

import { useEffect, useState } from "react";
import { fetchBackendStatus, type BackendStatusResponse } from "@/lib/apiClient";

const POLL_MS = 8000;

function statusLabel(reachable: boolean) {
  return reachable ? "reachable" : "error";
}

function statusClass(reachable: boolean) {
  return reachable ? "text-emerald-600" : "text-rose-600";
}

export default function BackendStatusPanel() {
  const [status, setStatus] = useState<BackendStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await fetchBackendStatus();
        if (!active) return;
        setStatus(data);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "status unavailable");
      }
    };
    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <section className="panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="panel-heading">Backend Status</p>
          <h3 className="mt-2 text-lg font-semibold text-ink-900">Live Service Health</h3>
          <p className="mt-1 text-sm text-ink-600">Polling every {POLL_MS / 1000}s. Failures are shown explicitly.</p>
        </div>
        {status ? <span className="pill">Last check: {status.timestamp}</span> : null}
      </div>

      {error ? (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {status ? (
          <>
            <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Postgres</p>
              <p className={`mt-2 text-sm font-semibold ${statusClass(status.services.postgres.reachable)}`}>
                {statusLabel(status.services.postgres.reachable)}
              </p>
              {status.services.postgres.detail ? (
                <p className="mt-1 text-xs text-ink-500">{status.services.postgres.detail}</p>
              ) : null}
            </div>
            <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">OpenSearch</p>
              <p className={`mt-2 text-sm font-semibold ${statusClass(status.services.opensearch.reachable)}`}>
                {statusLabel(status.services.opensearch.reachable)}
              </p>
              {status.services.opensearch.indexCount !== undefined ? (
                <p className="mt-1 text-xs text-ink-500">
                  plk_chunks_v1 count: {status.services.opensearch.indexCount}
                </p>
              ) : null}
              {status.services.opensearch.indices?.length ? (
                <p className="mt-1 text-xs text-ink-500">
                  Indices: {status.services.opensearch.indices.join(", ")}
                </p>
              ) : null}
              {status.services.opensearch.detail ? (
                <p className="mt-1 text-xs text-ink-500">{status.services.opensearch.detail}</p>
              ) : null}
            </div>
            <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Qdrant</p>
              <p className={`mt-2 text-sm font-semibold ${statusClass(status.services.qdrant.reachable)}`}>
                {statusLabel(status.services.qdrant.reachable)}
              </p>
              {status.services.qdrant.pointsCount !== undefined ? (
                <p className="mt-1 text-xs text-ink-500">
                  plk_chunks_v1 points: {status.services.qdrant.pointsCount}
                </p>
              ) : null}
              {status.services.qdrant.collections?.length ? (
                <p className="mt-1 text-xs text-ink-500">
                  Collections: {status.services.qdrant.collections.join(", ")}
                </p>
              ) : null}
              {status.services.qdrant.detail ? (
                <p className="mt-1 text-xs text-ink-500">{status.services.qdrant.detail}</p>
              ) : null}
            </div>
            <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">MinIO</p>
              <p className={`mt-2 text-sm font-semibold ${statusClass(status.services.minio.reachable)}`}>
                {statusLabel(status.services.minio.reachable)}
              </p>
              {status.services.minio.detail ? (
                <p className="mt-1 text-xs text-ink-500">{status.services.minio.detail}</p>
              ) : null}
            </div>
          </>
        ) : (
          <p className="text-sm text-ink-500">Loading status...</p>
        )}
      </div>
    </section>
  );
}
