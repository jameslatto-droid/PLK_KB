import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import EmptyState from "@/components/EmptyState";

export default function ArtefactsPage() {
  return (
    <PageShell pageKey="artefacts">
      <section className="panel">
        <p className="panel-heading">Artefacts</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Artefact Inventory</h2>
        <p className="mt-2 text-sm text-ink-600">
          Review registered artefacts, their versions, and whether access rules are attached.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Artefacts are the entry point for chunking. Missing access rules keep items denied by default.
        </p>
      </section>

      <StageStepper currentStep="chunking" />

      <EmptyState
        title="Artefacts will appear here"
        description="TODO: show artefact list, rule coverage, and chunking status for each artefact."
      />
    </PageShell>
  );
}
