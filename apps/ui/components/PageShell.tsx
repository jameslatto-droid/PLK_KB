"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { pipelineEventsByPage } from "@/lib/mockPipeline";
import { usePipelineLog } from "@/components/PipelineLogContext";
import type { PipelinePageKey } from "@/lib/mockPipeline";

type PageShellProps = {
  pageKey: PipelinePageKey;
  children: ReactNode;
};

export default function PageShell({ pageKey, children }: PageShellProps) {
  const { setEvents } = usePipelineLog();

  useEffect(() => {
    setEvents(pipelineEventsByPage[pageKey] ?? []);
  }, [pageKey, setEvents]);

  return <div className="flex flex-col gap-6">{children}</div>;
}
