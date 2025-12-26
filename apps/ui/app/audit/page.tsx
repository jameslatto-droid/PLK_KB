import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import EmptyState from "@/components/EmptyState";
import WhyPanel from "@/components/WhyPanel";

export default function AuditPage() {
  return (
    <PageShell pageKey="audit">
      <section className="panel">
        <p className="panel-heading">Audit / Decisions</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Explainable Authority Ledger</h2>
        <p className="mt-2 text-sm text-ink-600">
          Every allow or deny decision should be auditable, deterministic, and reason-coded.
        </p>
      </section>

      <section className="panel">
        <p className="panel-heading">Pipeline Context</p>
        <p className="mt-2 text-sm text-ink-600">
          Audit events are written after authority evaluation and must fail closed if logging fails.
        </p>
      </section>

      <StageStepper currentStep="authority" />

      <WhyPanel />

      <EmptyState
        title="Audit trail will appear here"
        description="TODO: surface query IDs, decision reasons, and matched rule IDs."
      />
    </PageShell>
  );
}
