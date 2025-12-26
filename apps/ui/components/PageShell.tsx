"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { pipelineEventsByPage } from "@/lib/mockPipeline";
import { usePipelineLog } from "@/components/PipelineLogContext";
import type { PipelinePageKey } from "@/lib/mockPipeline";

type PageShellProps = {
  pageKey: PipelinePageKey;
  children: ReactNode;
  useMock?: boolean;
};

export default function PageShell({ pageKey, children, useMock = true }: PageShellProps) {
  const { setEvents } = usePipelineLog();

  useEffect(() => {
    if (!useMock) return;
    setEvents(pipelineEventsByPage[pageKey] ?? []);
  }, [pageKey, setEvents, useMock]);

  return <div className="flex flex-col gap-6">{children}</div>;
}
