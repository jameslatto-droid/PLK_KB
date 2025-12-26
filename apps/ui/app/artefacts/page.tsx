import PageShell from "@/components/PageShell";
import ArtefactsPanel from "@/components/ArtefactsPanel";
import DatabaseStatsPanel from "@/components/DatabaseStatsPanel";

export default function ArtefactsPage() {
  return (
    <PageShell pageKey="artefacts" useMock={false}>
      <section className="panel">
        <p className="panel-heading">Artefacts</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Artefact Inventory</h2>
        <p className="mt-2 text-sm text-ink-600">
          Review registered artefacts, their versions, and index status across OpenSearch and Qdrant.
        </p>
      </section>

      <DatabaseStatsPanel />

      <ArtefactsPanel />
    </PageShell>
  );
}
