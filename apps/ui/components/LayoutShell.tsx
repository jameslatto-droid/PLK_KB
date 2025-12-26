"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import PipelineLogPanel from "@/components/PipelineLogPanel";
import { useUserContext } from "@/components/UserContext";

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
  const { active, presets, setActiveUser } = useUserContext();

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
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">Active User Context (dev-only)</p>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="pill">user: {active.actor}</span>
              <span className="pill">roles: {active.roles.join(", ")}</span>
              <span className="pill">classification: {active.classification}</span>
            </div>
            <label className="mt-2 flex items-center gap-2 text-xs font-semibold text-ink-600">
              Switch user:
              <select
                className="rounded-lg border border-ink-200 bg-white px-2 py-1 text-xs"
                value={active.id}
                onChange={(event) => setActiveUser(event.target.value)}
              >
                {presets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.label}
                  </option>
                ))}
              </select>
            </label>
            <p className="text-[11px] text-ink-500">No auth system yet — this only sets PLK_ACTOR / roles / classification for backend calls.</p>
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
