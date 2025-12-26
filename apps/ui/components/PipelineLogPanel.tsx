"use client";

import { useMemo, useState } from "react";
import { usePipelineLog } from "@/components/PipelineLogContext";

const statusStyles: Record<string, string> = {
  info: "bg-ink-400",
  ok: "bg-emerald-500",
  warn: "bg-amber-500",
  error: "bg-rose-500",
};

type PipelineLogPanelProps = {
  collapsed: boolean;
  onToggle: () => void;
};

export default function PipelineLogPanel({ collapsed, onToggle }: PipelineLogPanelProps) {
  const { events, clearEvents } = usePipelineLog();
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => a.ts.localeCompare(b.ts)),
    [events]
  );

  if (collapsed) {
    return (
      <div className="panel sticky top-6 h-fit">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-ink-700">Pipeline Log</p>
          <button
            type="button"
            className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold text-ink-700"
            onClick={onToggle}
          >
            Expand
          </button>
        </div>
        <p className="mt-4 text-xs text-ink-500">Collapsed. Expand to view recent events.</p>
      </div>
    );
  }

  return (
    <div className="panel sticky top-6 flex max-h-[calc(100vh-4rem)] flex-col">
      <div className="flex flex-shrink-0 items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-ink-700">Pipeline Log</p>
          <p className="text-xs text-ink-500">Visible stages with explainable decisions.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold text-ink-700"
            onClick={clearEvents}
          >
            Clear
          </button>
          <button
            type="button"
            className="rounded-full border border-ink-200 px-3 py-1 text-xs font-semibold text-ink-700"
            onClick={onToggle}
          >
            Collapse
          </button>
        </div>
      </div>

      <div className="mt-4 flex-1 space-y-4 overflow-y-auto">
        {sortedEvents.length === 0 ? (
          <p className="text-xs text-ink-500">No events yet. Run a pipeline action to populate this log.</p>
        ) : (
          sortedEvents.map((event, index) => (
            <div key={`${event.ts}-${event.stage}-${index}`} className="rounded-xl border border-ink-100/70 bg-white/70 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className={`mt-1 h-2.5 w-2.5 rounded-full ${statusStyles[event.status] ?? "bg-ink-400"}`} />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-400">
                      {event.stage}
                    </p>
                    <p className="text-sm font-medium text-ink-800">{event.message}</p>
                    <p className="text-xs text-ink-500">{event.ts}</p>
                  </div>
                </div>
                {event.details ? (
                  <button
                    type="button"
                    className="text-xs font-semibold text-ink-600"
                    onClick={() =>
                      setExpanded((prev) => ({
                        ...prev,
                        [index]: !prev[index],
                      }))
                    }
                  >
                    {expanded[index] ? "Hide" : "Details"}
                  </button>
                ) : null}
              </div>
              {event.details && expanded[index] ? (
                <div className="mt-2 rounded-lg border border-ink-100 bg-ink-50/60 p-2 text-xs text-ink-700">
                  {event.details}
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
