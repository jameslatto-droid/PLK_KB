"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useMemo, useState } from "react";
import type { PipelineEvent } from "@/lib/mockPipeline";

type PipelineLogContextValue = {
  events: PipelineEvent[];
  setEvents: (events: PipelineEvent[]) => void;
  clearEvents: () => void;
};

const PipelineLogContext = createContext<PipelineLogContextValue | undefined>(undefined);

export function PipelineLogProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<PipelineEvent[]>([]);

  const value = useMemo(
    () => ({
      events,
      setEvents,
      clearEvents: () => setEvents([]),
    }),
    [events]
  );

  return <PipelineLogContext.Provider value={value}>{children}</PipelineLogContext.Provider>;
}

export function usePipelineLog() {
  const context = useContext(PipelineLogContext);
  if (!context) {
    throw new Error("PipelineLogContext is missing from the component tree.");
  }
  return context;
}
