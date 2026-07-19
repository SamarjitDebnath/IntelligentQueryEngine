import { useState } from "react";
import { runEvaluation } from "../api/client";
import type { EvalReport } from "../types/api";

export function EvalPanel() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runEvaluation();
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="eval-panel">
      <div className="eval-header">
        <h2>Validation dataset</h2>
        <button type="button" onClick={run} disabled={loading}>
          {loading ? "Running…" : "Run evaluation"}
        </button>
      </div>
      {error && <p className="stage-error-msg">{error}</p>}
      {report && (
        <>
          <p className="eval-score">
            {report.passed}/{report.total} passed ({(report.accuracy * 100).toFixed(0)}% execution accuracy)
          </p>
          <ul className="eval-case-list">
            {report.cases.map((c) => (
              <li key={c.id} className={c.passed ? "stage-ok" : "stage-error"}>
                <div className="stage-header">
                  <span className="stage-name">
                    {c.passed ? "✓" : "✗"} {c.id}
                  </span>
                </div>
                <p className="plan-approach">{c.question}</p>
                {!c.passed && (
                  <details>
                    <summary>why it failed</summary>
                    <dl className="field-rows">
                      <div className="field-row">
                        <dt>expected sql</dt>
                        <dd>
                          <pre className="sql-block field-sql">{c.expected_sql}</pre>
                        </dd>
                      </div>
                      <div className="field-row">
                        <dt>generated sql</dt>
                        <dd>
                          {c.generated_sql ? (
                            <pre className="sql-block field-sql">{c.generated_sql}</pre>
                          ) : (
                            <span className="field-empty">none — pipeline errored first</span>
                          )}
                        </dd>
                      </div>
                      {c.error && (
                        <div className="field-row">
                          <dt>error</dt>
                          <dd>
                            <span className="stage-error-msg">{c.error}</span>
                          </dd>
                        </div>
                      )}
                    </dl>
                  </details>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
