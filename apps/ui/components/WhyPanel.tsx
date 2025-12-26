export default function WhyPanel() {
  return (
    <div className="panel">
      <p className="panel-heading">Why This Result?</p>
      <div className="mt-3 space-y-2 text-sm text-ink-700">
        <p>
          <span className="font-semibold">Allowed because:</span> TODO — surface authority rules and matched
          rule IDs.
        </p>
        <p>
          <span className="font-semibold">Blocked because:</span> TODO — surface denial reason codes and
          missing access rules.
        </p>
      </div>
    </div>
  );
}
