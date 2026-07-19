import { useState } from "react";
import { MarkdownText } from "./MarkdownText";
import type { QueryResponse } from "../types/api";

interface Props {
  result: QueryResponse;
}

export function ResultPanel({ result }: Props) {
  const [planOpen, setPlanOpen] = useState(false);
  const tableCount = Array.isArray(result.plan.tables) ? result.plan.tables.length : 0;

  return (
    <div className="result-panel">
      <div className="answer-card">
        <span className="label">Answer</span>
        <MarkdownText text={result.answer} />
      </div>

      {result.warnings.length > 0 && (
        <div className="warnings">
          {result.warnings.map((w, i) => (
            <div key={i} className="warning-chip">
              ⚠ {w}
            </div>
          ))}
        </div>
      )}

      {result.plan.approach && (
        <>
          <div className="dag">
            <button
              type="button"
              className={`dag-node stage-ok ${planOpen ? "selected" : ""}`}
              onClick={() => setPlanOpen(true)}
              title={result.plan.approach}
            >
              <span className="dag-node-icon">◆</span>
              <span className="dag-node-name">plan</span>
              <span className="dag-node-duration">
                {tableCount > 0 ? `${tableCount} table${tableCount === 1 ? "" : "s"}` : "details"}
              </span>
            </button>
          </div>
          {planOpen && (
            <div className="dag-detail">
              <MarkdownText text={result.plan.approach} className="plan-approach" />
              {tableCount > 0 && <p className="plan-tables">Tables: {(result.plan.tables as string[]).join(", ")}</p>}
            </div>
          )}
        </>
      )}

      <details className="detail-block">
        <summary>Generated SQL</summary>
        <pre className="sql-block">{result.sql}</pre>
      </details>

      <details className="detail-block">
        <summary>
          Result rows ({result.rows.length})
        </summary>
        {result.rows.length === 0 ? (
          <p className="empty-note">No rows returned.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {result.columns.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j}>{String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
    </div>
  );
}
