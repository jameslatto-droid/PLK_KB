"use client";

import { useEffect, useState } from "react";
import { fetchAccessRules, seedAccessRules, type AccessRuleRecord } from "@/lib/apiClient";
import { useUserContext } from "@/components/UserContext";

export default function AccessRulesPanel() {
  const [rules, setRules] = useState<AccessRuleRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const { active } = useUserContext();

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchAccessRules();
      setRules(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const seed = async () => {
    setSeeding(true);
    try {
      await seedAccessRules({
        actor: active.actor,
        roles: active.roles,
        classification: active.classification,
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to seed rules");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <section className="panel">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="panel-heading">Access Rules</p>
          <h3 className="mt-2 text-lg font-semibold text-ink-900">Minimal internal model</h3>
          <p className="mt-1 text-sm text-ink-600">SUPERUSER matches any classification. USER matches classification=REFERENCE.</p>
          <p className="mt-1 text-xs text-ink-500">Actor: {active.actor} · Roles: {active.roles.join(", ")} · Classification: {active.classification}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-full border border-ink-200 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ink-700"
            onClick={load}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
          <button
            type="button"
            className="rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white"
            onClick={seed}
            disabled={seeding}
          >
            {seeding ? "Seeding..." : "Seed Minimal Rules"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm text-ink-700">
          <thead>
            <tr className="border-b border-ink-100 text-xs uppercase tracking-[0.15em] text-ink-500">
              <th className="px-2 py-2">rule_id</th>
              <th className="px-2 py-2">document_id</th>
              <th className="px-2 py-2">title</th>
              <th className="px-2 py-2">classification</th>
              <th className="px-2 py-2">roles</th>
              <th className="px-2 py-2">project</th>
              <th className="px-2 py-2">discipline</th>
              <th className="px-2 py-2">commercial</th>
              <th className="px-2 py-2">created_at</th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 ? (
              <tr>
                <td className="px-2 py-3 text-sm text-ink-500" colSpan={9}>
                  {loading ? "Loading rules..." : "No rules yet. Seed minimal rules to enable access."}
                </td>
              </tr>
            ) : (
              rules.map((rule) => (
                <tr key={rule.rule_id} className="border-b border-ink-50">
                  <td className="px-2 py-2 text-xs text-ink-600">{rule.rule_id}</td>
                  <td className="px-2 py-2 font-mono text-[11px] text-ink-800">{rule.document_id}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.title}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.classification ?? "ANY"}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.allowed_roles.join(", ")}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.project_code ?? "—"}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.discipline ?? "—"}</td>
                  <td className="px-2 py-2 text-xs text-ink-700">{rule.commercial_sensitivity ?? "—"}</td>
                  <td className="px-2 py-2 text-xs text-ink-600">{rule.created_at}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
