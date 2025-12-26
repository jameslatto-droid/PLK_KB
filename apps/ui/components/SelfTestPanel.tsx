"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchSelfTest, startSelfTestWithContext, type SelfTestRun } from "@/lib/apiClient";
import { usePipelineLog } from "@/components/PipelineLogContext";
import { useUserContext } from "@/components/UserContext";

const POLL_MS = 1500;

export default function SelfTestPanel() {
  const [run, setRun] = useState<SelfTestRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const { setEvents } = usePipelineLog();
  const { active } = useUserContext();

  useEffect(() => {
    if (!run) return;
    setEvents(run.events ?? []);
  }, [run, setEvents]);

  useEffect(() => {
    if (!run || run.status !== "running") return;
    let active = true;
    const poll = async () => {
      try {
        const updated = await fetchSelfTest(run.runId);
        if (!active) return;
        setRun(updated);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "self-test polling failed");
      }
    };
    const timer = setInterval(poll, POLL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [run]);

  const start = async () => {
    setStarting(true);
    try {
      const nextRun = await startSelfTestWithContext({
        actor: active.actor,
        roles: active.roles,
        classification: active.classification,
      });
      setRun(nextRun);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "self-test failed to start");
    } finally {
      setStarting(false);
    }
  };

  const verdict = useMemo(() => {
    if (!run) return "IDLE";
    if (run.status === "running") return "RUNNING";
    return run.status === "pass" ? "PASS" : "FAIL";
  }, [run]);

  return (
    <section className="panel">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="panel-heading">System Self-Test</p>
          <h3 className="mt-2 text-lg font-semibold text-ink-900">Live Pipeline Verification</h3>
          <p className="mt-1 text-sm text-ink-600">
            Uses the internal fixture at /home/jim/PLK_KB/ops/scripts/stage5_tmp. No user data is touched.
          </p>
          <p className="mt-1 text-xs text-ink-500">Actor: {active.actor} · Roles: {active.roles.join(", ")} · Classification: {active.classification}</p>
        </div>
        <button
          type="button"
          className="rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white"
          onClick={start}
          disabled={starting || run?.status === "running"}
        >
          {starting || run?.status === "running" ? "Running..." : "Run System Self-Test"}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Run ID</p>
          <p className="mt-2 text-sm text-ink-700">{run?.runId ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Status</p>
          <p className="mt-2 text-sm font-semibold text-ink-900">{verdict}</p>
          {run?.lastError ? <p className="mt-1 text-xs text-rose-600">{run.lastError}</p> : null}
        </div>
        <div className="rounded-xl border border-ink-100 bg-white/70 p-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">Artefacts</p>
          <p className="mt-2 text-sm text-ink-700">{run?.artefacts.length ?? 0} processed</p>
          {run?.searchSummary ? (
            <p className="mt-1 text-xs text-ink-500">Search results: {run.searchSummary.resultCount}</p>
          ) : null}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {(run?.events ?? []).length === 0 ? (
          <p className="text-sm text-ink-500">No self-test events yet. Run the self-test to see progress.</p>
        ) : (
          run?.events.map((event, idx) => (
            <div key={`${event.ts}-${idx}`} className="rounded-xl border border-ink-100 bg-white/70 p-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">{event.stage}</p>
                  <p className="text-sm font-medium text-ink-800">{event.message}</p>
                  <p className="text-xs text-ink-500">{event.ts}</p>
                </div>
                <span className="pill">{event.status}</span>
              </div>
              {event.details ? <p className="mt-2 text-xs text-ink-600">{event.details}</p> : null}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
