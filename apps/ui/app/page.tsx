import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import EmptyState from "@/components/EmptyState";

export default function DashboardPage() {
  return (
    <PageShell pageKey="dashboard">
      <section className="panel">
        <p className="panel-heading">Dashboard</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Visible Pipeline Overview</h2>
        <p className="mt-2 text-sm text-ink-600">
          Track ingestion, indexing, authority checks, and explainable responses in one place.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          This page surfaces system-wide state across ingestion, indexing, authority, and response assembly.
        </p>
      </section>

      <StageStepper currentStep="response" />

      <EmptyState
        title="Pipeline telemetry will appear here"
        description="TODO: wire live system summaries, active jobs, and last audit decisions. No API calls yet."
      />
    </PageShell>
  );
}
