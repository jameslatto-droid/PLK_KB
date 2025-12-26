"use client";

import { useEffect, useState } from "react";
import { fetchBackendStatus, type BackendStatusResponse } from "@/lib/apiClient";

export default function DatabaseStatsPanel() {
  const [status, setStatus] = useState<BackendStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchBackendStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading && !status) {
    return (
      <section className="panel">
        <p className="text-sm text-ink-500">Loading database statistics...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      </section>
    );
  }

  if (!status) return null;

  const opensearch = status.services.opensearch;
  const qdrant = status.services.qdrant;
  const postgres = status.services.postgres;
  const minio = status.services.minio;

  return (
    <section className="panel">
      <div className="flex items-center justify-between">
        <div>
          <p className="panel-heading">Database Statistics</p>
          <p className="mt-1 text-sm text-ink-600">
            Overall system metrics from PostgreSQL, OpenSearch, and Qdrant.
          </p>
        </div>
        <button
          type="button"
          className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold text-ink-700 hover:bg-ink-50 disabled:opacity-50"
          onClick={load}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        {/* PostgreSQL */}
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                postgres.reachable ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink-400">
              PostgreSQL
            </p>
          </div>
          <p className="mt-2 text-sm font-semibold text-ink-900">
            {postgres.reachable ? "Connected" : "Unreachable"}
          </p>
          {postgres.detail ? (
            <p className="mt-1 text-xs text-rose-600">{postgres.detail}</p>
          ) : null}
        </div>

        {/* OpenSearch */}
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                opensearch.reachable ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink-400">
              OpenSearch
            </p>
          </div>
          <p className="mt-2 text-2xl font-bold text-ink-900">
            {opensearch.indexCount?.toLocaleString() ?? "—"}
          </p>
          <p className="text-xs text-ink-500">indexed chunks</p>
          {opensearch.detail ? (
            <p className="mt-1 text-xs text-rose-600">{opensearch.detail}</p>
          ) : null}
        </div>

        {/* Qdrant */}
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                qdrant.reachable ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink-400">
              Qdrant
            </p>
          </div>
          <p className="mt-2 text-2xl font-bold text-ink-900">
            {qdrant.pointsCount?.toLocaleString() ?? "—"}
          </p>
          <p className="text-xs text-ink-500">vector points</p>
          {qdrant.detail ? (
            <p className="mt-1 text-xs text-rose-600">{qdrant.detail}</p>
          ) : null}
        </div>

        {/* MinIO */}
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                minio.reachable ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink-400">
              MinIO
            </p>
          </div>
          <p className="mt-2 text-sm font-semibold text-ink-900">
            {minio.reachable ? "Connected" : "Unreachable"}
          </p>
          {minio.detail ? (
            <p className="mt-1 text-xs text-rose-600">{minio.detail}</p>
          ) : null}
        </div>
      </div>

      <div className="mt-2 text-xs text-ink-500">
        Last updated: {new Date(status.timestamp).toLocaleString()}
      </div>
    </section>
  );
}
