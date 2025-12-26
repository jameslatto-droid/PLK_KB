"use client";

import { useEffect, useMemo, useState } from "react";

import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import { useUserContext } from "@/components/UserContext";

type AuditEntry = {
  audit_id: number;
  actor: string;
  action: string;
  document_id?: string | null;
  version_id?: string | null;
  model_version?: string | null;
  index_version?: string | null;
  details?: Record<string, any> | null;
  created_at: string;
};

type ApiResponse = {
  entries: AuditEntry[];
  total: number;
  page: number;
  limit: number;
  actors: string[];
  error?: string;
};

type Filters = {
  actor: string;
  start: string;
  end: string;
  decision: "ALL" | "ALLOW" | "DENY";
};

const PAGE_LIMIT = 50;

function decisionFromDetails(details?: Record<string, any> | null): "ALLOW" | "DENY" | null {
  if (!details) return null;
  const decision = details?.decision;
  if (decision && typeof decision === "object") {
    const value = (decision as Record<string, unknown>)["decision"];
    if (value === "ALLOW" || value === "DENY") return value;
  }
  return null;
}

function querySummary(details?: Record<string, any> | null): string {
  if (!details) return "—";
  if (typeof details.query === "string" && details.query.trim()) return details.query.trim();
  if (typeof details.query_text === "string" && details.query_text.trim()) return details.query_text.trim();
  if (typeof details.action === "string") return details.action;
  if (typeof details.query_id === "string") return `query_id=${details.query_id}`;
  return "—";
}

function resultCount(details?: Record<string, any> | null): string {
  if (!details) return "—";
  if (typeof details.result_count === "number") return String(details.result_count);
  return "—";
}

export default function AuditPage() {
  const { active } = useUserContext();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [actors, setActors] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>({
    actor: "",
    start: "",
    end: "",
    decision: "ALL",
  });

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_LIMIT)), [total]);

  useEffect(() => {
    fetchAudit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const applyFilters = () => {
    setPage(1);
    fetchAudit(1);
  };

  async function fetchAudit(forcedPage?: number) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(forcedPage ?? page),
        limit: String(PAGE_LIMIT),
      });
      if (filters.actor) params.set("actor", filters.actor);
      if (filters.start) params.set("start", filters.start);
      if (filters.end) params.set("end", filters.end);
      if (filters.decision !== "ALL") params.set("decision", filters.decision);

      const res = await fetch(`/api/audit?${params.toString()}`);
      if (!res.ok) {
        const payload = (await res.json().catch(() => ({}))) as ApiResponse;
        throw new Error(payload.error || `Request failed with ${res.status}`);
      }
      const data = (await res.json()) as ApiResponse;
      setEntries(data.entries || []);
      setTotal(Number(data.total || 0));
      setActors(data.actors || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell pageKey="audit" useMock={false}>
      <section className="panel">
        <p className="panel-heading">Audit</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Traceability & Evidence</h2>
        <p className="mt-2 text-sm text-ink-600">
          Read-only view of the audit log captured by the pipeline. Entries are fail-closed; missing audit records
          indicate a blocking error.
        </p>
        <p className="mt-2 text-xs text-ink-500">
          Active context: {active.actor} — Roles: {active.roles.join(", ")} — Classification: {active.classification}
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Audit events are written at every stage: query received, authority evaluation, and results returned. No
          deletes or edits are permitted.
        </p>
      </section>

      <StageStepper currentStep="authority" />

      <section className="panel space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="panel-heading">Filters</p>
            <p className="mt-1 text-xs text-ink-500">Actor list is sourced from all audit records, not just the current page.</p>
          </div>
          <button
            type="button"
            onClick={applyFilters}
            className="rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white"
          >
            Apply Filters
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <label className="flex flex-col gap-1 text-sm text-ink-700">
            Actor
            <select
              value={filters.actor}
              onChange={(e) => setFilters((prev) => ({ ...prev, actor: e.target.value }))}
              className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
            >
              <option value="">All actors</option>
              {actors.map((actor) => (
                <option key={actor} value={actor}>
                  {actor}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-700">
            Start (UTC)
            <input
              type="datetime-local"
              value={filters.start}
              onChange={(e) => setFilters((prev) => ({ ...prev, start: e.target.value }))}
              className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-700">
            End (UTC)
            <input
              type="datetime-local"
              value={filters.end}
              onChange={(e) => setFilters((prev) => ({ ...prev, end: e.target.value }))}
              className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-700">
            Decision
            <select
              value={filters.decision}
              onChange={(e) => setFilters((prev) => ({ ...prev, decision: e.target.value as Filters["decision"] }))}
              className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm"
            >
              <option value="ALL">All</option>
              <option value="ALLOW">ALLOW</option>
              <option value="DENY">DENY</option>
            </select>
          </label>
        </div>

        {error ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            Audit log unavailable: {error}
          </div>
        ) : null}

        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white/70">
          <table className="min-w-full divide-y divide-ink-100">
            <thead className="bg-ink-50/60 text-left text-xs uppercase tracking-[0.2em] text-ink-500">
              <tr>
                  <th className="px-4 py-3" title="Audit record creation time (created_at)">Audit time</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Decision</th>
                <th className="px-4 py-3">Details</th>
                <th className="px-4 py-3">Results</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100 text-sm text-ink-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-sm text-ink-500">
                    Loading audit log...
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-sm text-ink-500">
                    No audit entries found.
                  </td>
                </tr>
              ) : (
                entries.map((entry) => {
                  const decision = decisionFromDetails(entry.details);
                  return (
                    <tr key={entry.audit_id}>
                      <td className="px-4 py-3 align-top text-xs text-ink-600">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <div className="font-semibold text-ink-900">{entry.actor}</div>
                        <div className="text-xs text-ink-500">audit_id: {entry.audit_id}</div>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <span className="rounded-full bg-ink-100 px-2 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-ink-700">
                          {entry.action}
                        </span>
                        {entry.document_id ? (
                          <div className="mt-1 text-xs text-ink-500">doc: {entry.document_id}</div>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 align-top">
                        {decision ? (
                          <span
                            className={`rounded-full px-2 py-1 text-xs font-semibold ${
                              decision === "ALLOW" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-700"
                            }`}
                          >
                            {decision}
                          </span>
                        ) : (
                          <span className="text-xs text-ink-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top text-sm text-ink-800">
                        <div className="max-w-xl break-words" title={querySummary(entry.details)}>
                          {querySummary(entry.details)}
                        </div>
                        {entry.details?.decision?.reasons?.length ? (
                          <div className="mt-1 text-xs text-ink-500">
                            Reasons: {(entry.details.decision.reasons as string[]).join(", ")}
                          </div>
                        ) : null}
                        {entry.details?.query_id ? (
                          <div className="mt-1 text-xs text-ink-500">query_id: {entry.details.query_id}</div>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 align-top text-sm text-ink-800">{resultCount(entry.details)}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-ink-700">
          <div>
            Showing {(page - 1) * PAGE_LIMIT + (entries.length ? 1 : 0)}–
            {(page - 1) * PAGE_LIMIT + entries.length} of {total} entries
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-ink-700 disabled:opacity-50"
            >
              Prev
            </button>
            <span className="text-xs text-ink-600">
              Page {page} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-ink-700 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </PageShell>
  );
}
