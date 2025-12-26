import PageShell from "@/components/PageShell";
import StageStepper from "@/components/StageStepper";
import WhyPanel from "@/components/WhyPanel";
import AccessRulesPanel from "@/components/AccessRulesPanel";

export default function AuditPage() {
  return (
    <PageShell pageKey="audit" useMock={false}>
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

      <AccessRulesPanel />

      <WhyPanel />
    </PageShell>
  );
}
