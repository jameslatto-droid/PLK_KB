"use client";

import { useEffect, useState } from "react";
import { getArtefactDetail, listArtefacts, type ArtefactDetail, type ArtefactRecord } from "@/lib/apiClient";

export default function ArtefactsPanel() {
  const [artefacts, setArtefacts] = useState<ArtefactRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ArtefactDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await listArtefacts();
      setArtefacts(data);
      setError(null);
      if (data.length && !selectedId) {
        setSelectedId(data[0].artefact_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load artefacts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const fetchDetail = async () => {
      setLoadingDetail(true);
      try {
        const data = await getArtefactDetail(selectedId);
        setDetail(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "failed to load artefact detail");
      } finally {
        setLoadingDetail(false);
      }
    };
    fetchDetail();
  }, [selectedId]);

  return (
    <section className="panel">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="panel-heading">Artefact Inventory</p>
          <h3 className="mt-2 text-lg font-semibold text-ink-900">Registered + indexed assets</h3>
          <p className="mt-1 text-sm text-ink-600">Read-only view sourced from Postgres. Index presence is checked live against OpenSearch and Qdrant.</p>
        </div>
        <button
          type="button"
          className="rounded-full border border-ink-200 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ink-700"
          onClick={load}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error ? (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-xl border border-ink-100 bg-white/70">
          <div className="flex items-center justify-between px-3 py-2 text-xs uppercase tracking-[0.15em] text-ink-500">
            <span>Artefacts</span>
            <span>{artefacts.length}</span>
          </div>
          <div className="divide-y divide-ink-100 max-h-[480px] overflow-y-auto">
            {artefacts.length === 0 ? (
              <p className="px-3 py-3 text-sm text-ink-500">{loading ? "Loading..." : "No artefacts found."}</p>
            ) : (
              artefacts.map((item) => {
                const active = item.artefact_id === selectedId;
                return (
                  <button
                    key={item.artefact_id}
                    type="button"
                    onClick={() => setSelectedId(item.artefact_id)}
                    className={`flex w-full flex-col items-start gap-1 px-3 py-2 text-left ${
                      active ? "bg-ink-900/5" : "hover:bg-ink-50"
                    }`}
                  >
                    <div className="flex w-full items-center justify-between text-sm text-ink-800">
                      <span className="font-semibold">{item.title}</span>
                      <span className="pill">{item.artefact_type}</span>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs text-ink-500">
                      <span className="pill">artefact: {item.artefact_id}</span>
                      <span className="pill">doc: {item.document_id}</span>
                      <span className="pill">version: {item.version_id}</span>
                      <span className="pill">chunks: {item.chunk_count}</span>
                    </div>
                    <p className="text-xs text-ink-500">storage: {item.storage_path}</p>
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div className="rounded-xl border border-ink-100 bg-white/70 p-4">
          <p className="panel-heading">Detail</p>
          {loadingDetail ? <p className="text-sm text-ink-500">Loading detail...</p> : null}
          {!detail && !loadingDetail ? <p className="text-sm text-ink-500">Select an artefact to inspect.</p> : null}
          {detail ? (
            <div className="mt-2 space-y-2 text-sm text-ink-700">
              <div className="flex flex-wrap gap-2 text-xs text-ink-500">
                <span className="pill">artefact: {detail.artefact_id}</span>
                <span className="pill">doc: {detail.document_id}</span>
                <span className="pill">version: {detail.version_id}</span>
              </div>
              <p className="text-xs text-ink-500">storage: {detail.storage_path}</p>
              <p className="text-xs text-ink-500">authority level: {detail.authority_level}</p>
              <div className="grid gap-2 md:grid-cols-2">
                <div className="rounded-lg border border-ink-100 bg-ink-50/60 p-3 text-xs text-ink-700">
                  <p className="font-semibold">Ingestion</p>
                  <p>chunk count: {detail.chunk_count}</p>
                  <p>created_at: {detail.created_at}</p>
                </div>
                <div className="rounded-lg border border-ink-100 bg-ink-50/60 p-3 text-xs text-ink-700">
                  <p className="font-semibold">Index presence</p>
                  <p>OpenSearch count: {detail.opensearch_count ?? 0}</p>
                  <p>Qdrant count: {detail.qdrant_count ?? 0}</p>
                  <p>last indexed: {detail.last_indexed_at ?? "not tracked"}</p>
                  {detail.opensearch_error ? (
                    <p className="text-rose-600">OS error: {detail.opensearch_error}</p>
                  ) : null}
                  {detail.qdrant_error ? (
                    <p className="text-rose-600">Qdrant error: {detail.qdrant_error}</p>
                  ) : null}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
