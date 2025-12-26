import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import WhyPanel from "@/components/WhyPanel";
import SearchPanel from "@/components/SearchPanel";

export default function SearchPage() {
  return (
    <PageShell pageKey="search" useMock={false}>
      <section className="panel">
        <p className="panel-heading">Search</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Explainable Hybrid Search</h2>
        <p className="mt-2 text-sm text-ink-600">
          Combine lexical and semantic signals, then apply authority gating before returning results.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Search results are filtered by authority after retrieval. Every allow or deny decision must be
          explainable.
        </p>
      </section>

      <StageStepper currentStep="search" />

      <WhyPanel />

      <SearchPanel />
    </PageShell>
  );
}
