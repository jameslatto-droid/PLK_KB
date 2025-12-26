import PageShell from "@/components/PageShell";
import IngestionPanel from "@/components/IngestionPanel";

export default function IngestPage() {
  return (
    <PageShell pageKey="ingest" useMock={false}>
      <section className="panel">
        <p className="panel-heading">Ingest</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Register New Artefacts</h2>
        <p className="mt-2 text-sm text-ink-600">
          Capture artefacts, register metadata, and open the pipeline for downstream chunking.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Ingestion and metadata registration occur here. Successful registration unlocks chunking and
          indexing.
        </p>
      </section>

      <IngestionPanel />
    </PageShell>
  );
}
