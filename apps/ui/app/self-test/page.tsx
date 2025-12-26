import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import SelfTestPanel from "@/components/SelfTestPanel";

export default function SelfTestPage() {
  return (
    <PageShell pageKey="self-test" useMock={false}>
      <section className="panel">
        <p className="panel-heading">System Self-Test</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Deterministic Pipeline Validation</h2>
        <p className="mt-2 text-sm text-ink-600">
          Run a smoke test across ingestion, indexing, authority, and response contracts.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Self-tests verify that each stage can run end-to-end without violating fail-closed guarantees.
        </p>
      </section>

      <StageStepper currentStep="response" />

      <SelfTestPanel />
    </PageShell>
  );
}
