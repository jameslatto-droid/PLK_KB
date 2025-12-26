"use client";

import { useEffect, useMemo, useState } from "react";
import {
  fetchBackendStatus,
  runSearchWithContext,
  type BackendStatusResponse,
  type SearchResponse,
} from "@/lib/apiClient";
import { usePipelineLog } from "@/components/PipelineLogContext";
import { useUserContext } from "@/components/UserContext";

export default function SearchPanel() {
  const [query, setQuery] = useState("deployment test");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [status, setStatus] = useState<BackendStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { setEvents } = usePipelineLog();
  const { active } = useUserContext();

  useEffect(() => {
    let active = true;
    const loadStatus = async () => {
      try {
        const data = await fetchBackendStatus();
        if (!active) return;
        setStatus(data);
      } catch {
        if (!active) return;
        setStatus(null);
      }
    };
    loadStatus();
    return () => {
      active = false;
    };
  }, []);

  const emptyReason = useMemo(() => {
    if (!response) return null;
    if (response.response.results.length > 0) return null;
    if (status?.services.opensearch.indexCount === 0 || status?.services.qdrant.pointsCount === 0) {
      return "No indexed content available yet. Indexing must complete before results appear.";
    }
    if ((response.authority_summary?.denied ?? 0) > 0) {
      return "No results returned due to authority rules (deny-by-default enforced).";
    }
    return "No results matched this query.";
  }, [response, status]);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runSearchWithContext(query, {
        actor: active.actor,
        roles: active.roles,
        classification: active.classification,
      });
      setResponse(result);
      const now = new Date().toISOString();
      setEvents([
        {
          ts: now,
          stage: "SEARCH",
          status: "ok",
          message: `Hybrid search for: ${result.response.query} (actor=${active.actor})`,
          details: `query_id=${result.response.query_id} roles=${active.roles.join(",")}`,
        },
        {
          ts: now,
          stage: "AUTHORITY",
          status: "ok",
          message: `Authority evaluated: allowed=${result.authority_summary?.allowed ?? 0} denied=${
            result.authority_summary?.denied ?? 0
          }`,
        },
        {
          ts: now,
          stage: "RESPONSE",
          status: "ok",
          message: `Response returned ${result.response.results.length} results`,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
      setEvents([
        {
          ts: new Date().toISOString(),
          stage: "SEARCH",
          status: "error",
          message: "Search failed",
          details: err instanceof Error ? err.message : "unknown error",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <p className="panel-heading">Search Console</p>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-ink-500">
        <span className="pill">actor: {active.actor}</span>
        <span className="pill">roles: {active.roles.join(", ")}</span>
        <span className="pill">classification: {active.classification}</span>
        <span className="pill">dev-only context switcher in header</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="flex-1 rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
          placeholder="Enter a query"
        />
        <button
          type="button"
          className="rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white"
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? "Searching..." : "Run Search"}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : null}

      {response ? (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-center gap-3 text-xs text-ink-500">
            <span className="pill">query_id: {response.response.query_id}</span>
            <span className="pill">results: {response.response.results.length}</span>
            <span className="pill">timestamp: {response.response.timestamp}</span>
          </div>
          {emptyReason ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              {emptyReason}
            </div>
          ) : null}
          <div className="space-y-4">
            {response.response.results.map((result) => (
              <div key={result.chunk_id} className="rounded-xl border border-ink-100 bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">{result.chunk_id}</p>
                    <p className="text-sm text-ink-600">document_id: {result.document_id}</p>
                  </div>
                  <div className="text-xs text-ink-500">
                    final {result.scores.final.toFixed(4)} | lex {result.scores.lexical.toFixed(4)} | sem{" "}
                    {result.scores.semantic.toFixed(4)}
                  </div>
                </div>
                <p className="mt-3 text-sm text-ink-800">{result.snippet}</p>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-ink-100 bg-ink-50/60 p-3 text-xs text-ink-700">
                    <p className="font-semibold">Authority</p>
                    <p>decision: {result.authority.decision}</p>
                    <p>matched_rule_ids: {result.authority.matched_rule_ids.join(", ") || "—"}</p>
                  </div>
                  <div className="rounded-xl border border-ink-100 bg-ink-50/60 p-3 text-xs text-ink-700">
                    <p className="font-semibold">Explanation</p>
                    <p>{result.explanation.why_matched}</p>
                    <p>{result.explanation.why_allowed}</p>
                    <p>{result.explanation.why_ranked}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-ink-500">No search executed yet. Run a query to see results.</p>
      )}
    </section>
  );
}
