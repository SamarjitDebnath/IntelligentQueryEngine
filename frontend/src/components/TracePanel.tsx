import { useEffect, useState } from "react";
import { DetailFields } from "./DetailFields";
import type { TraceDetail } from "../types/api";

interface Props {
  trace: TraceDetail | null;
  loading: boolean;
}

function statusClass(status: string): string {
  if (status === "ok") return "stage-ok";
  if (status === "error") return "stage-error";
  return "stage-running";
}

function statusIcon(status: string): string {
  if (status === "ok") return "●";
  if (status === "error") return "✗";
  return "…";
}

export function TracePanel({ trace, loading }: Props) {
  const [selected, setSelected] = useState<number | null>(null);

  // Land on the failing node (if any) by default, otherwise the first node —
  // keeps the DAG at "minimal" until a node is deliberately picked.
  useEffect(() => {
    if (!trace) {
      setSelected(null);
      return;
    }
    const failedIndex = trace.stages.findIndex((s) => s.status === "error");
    setSelected(failedIndex >= 0 ? failedIndex : 0);
  }, [trace]);

  if (loading) return <p className="empty-note">Loading trace…</p>;
  if (!trace) return <p className="empty-note">Run a query to see its pipeline trace.</p>;

  const activeStage = selected !== null ? trace.stages[selected] : null;

  return (
    <div className="trace-panel">
      <div className="trace-summary">
        <span className={`trace-status ${statusClass(trace.status)}`}>{trace.status}</span>
        <span>{trace.total_duration_ms?.toFixed(1)} ms total</span>
      </div>

      <div className="dag">
        {trace.stages.map((stage, i) => (
          <span key={i} className="dag-step">
            <button
              type="button"
              className={`dag-node ${statusClass(stage.status)} ${selected === i ? "selected" : ""}`}
              onClick={() => setSelected(i)}
              title={stage.name}
            >
              <span className="dag-node-icon">{statusIcon(stage.status)}</span>
              <span className="dag-node-name">{stage.name}</span>
              <span className="dag-node-duration">{stage.duration_ms?.toFixed(0)} ms</span>
            </button>
            {i < trace.stages.length - 1 && <span className="dag-edge">→</span>}
          </span>
        ))}
      </div>

      {activeStage && (
        <div className="dag-detail">
          <div className="stage-header">
            <span className="stage-name">{activeStage.name}</span>
            <span className="stage-duration">{activeStage.duration_ms?.toFixed(1)} ms</span>
          </div>
          {activeStage.error && <p className="stage-error-msg">{activeStage.error}</p>}
          {activeStage.input != null && (
            <div className="detail-section">
              <span className="detail-section-label">input</span>
              <DetailFields data={activeStage.input} />
            </div>
          )}
          {activeStage.output != null && (
            <div className="detail-section">
              <span className="detail-section-label">output</span>
              <DetailFields data={activeStage.output} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
