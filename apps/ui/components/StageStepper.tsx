type PipelineStep =
  | "ingestion"
  | "chunking"
  | "indexing-text"
  | "indexing-vector"
  | "search"
  | "authority"
  | "response";

type StageStepperProps = {
  currentStep: PipelineStep;
};

const steps: { id: PipelineStep; label: string; hint: string }[] = [
  { id: "ingestion", label: "Ingestion", hint: "Files enter the pipeline" },
  { id: "chunking", label: "Chunking", hint: "Split into searchable units" },
  { id: "indexing-text", label: "Indexing (Text)", hint: "OpenSearch lexical index" },
  { id: "indexing-vector", label: "Indexing (Vector)", hint: "Qdrant semantic vectors" },
  { id: "search", label: "Search", hint: "Hybrid retrieval" },
  { id: "authority", label: "Authority", hint: "Allow/deny gating" },
  { id: "response", label: "Response", hint: "Explainable output" },
];

export default function StageStepper({ currentStep }: StageStepperProps) {
  return (
    <div className="panel">
      <p className="panel-heading">Pipeline Stepper</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {steps.map((step) => {
          const isActive = step.id === currentStep;
          return (
            <div
              key={step.id}
              className={`rounded-xl border px-3 py-2 ${
                isActive
                  ? "border-ember-300 bg-ember-50 text-ember-700"
                  : "border-ink-100 bg-white/60 text-ink-700"
              }`}
            >
              <p className="text-sm font-semibold">{step.label}</p>
              <p className="text-xs opacity-80">{step.hint}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
