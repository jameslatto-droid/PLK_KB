"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import PipelineLogPanel from "@/components/PipelineLogPanel";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/ingest", label: "Ingest" },
  { href: "/artefacts", label: "Artefacts" },
  { href: "/search", label: "Search" },
  { href: "/self-test", label: "System Self-Test" },
  { href: "/audit", label: "Audit / Decisions" },
];

export default function LayoutShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [logCollapsed, setLogCollapsed] = useState(false);

  return (
    <div className="min-h-screen px-6 py-6">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-6">
        <header className="panel flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-ink-400">PLK_KB</p>
              <h1 className="text-lg font-semibold text-ink-900">Visible Pipeline Console</h1>
            </div>
            <span className="badge">local</span>
          </div>
          <div className="panel flex flex-col gap-2 bg-white/60 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">Current Context</p>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="pill">user: jim</span>
              <span className="pill">roles: SUPERUSER</span>
              <span className="pill">classification: REFERENCE</span>
            </div>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)_320px]">
          <aside className="panel flex flex-col gap-2 self-start">
            <p className="panel-heading">Navigation</p>
            <nav className="mt-2 flex flex-col gap-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-ink-900 text-white"
                        : "text-ink-700 hover:bg-ink-50 hover:text-ink-900"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </aside>

          <main className="flex flex-col gap-6">{children}</main>

          <aside className="hidden lg:block">
            <PipelineLogPanel collapsed={logCollapsed} onToggle={() => setLogCollapsed(!logCollapsed)} />
          </aside>
        </div>

        <div className="lg:hidden">
          <PipelineLogPanel collapsed={logCollapsed} onToggle={() => setLogCollapsed(!logCollapsed)} />
        </div>
      </div>
    </div>
  );
}
