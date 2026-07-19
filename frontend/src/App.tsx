import { useEffect, useState } from "react";
import { ApiError, getSchema, getSuggestions, getTrace, runQuery } from "./api/client";
import { EvalPanel } from "./components/EvalPanel";
import { MenuPanel, type Tab } from "./components/MenuPanel";
import { QueryForm } from "./components/QueryForm";
import { ResultPanel } from "./components/ResultPanel";
import { TracePanel } from "./components/TracePanel";
import type { QueryResponse, SchemaTable, TraceDetail } from "./types/api";
import "./App.css";

const FALLBACK_SUGGESTIONS = [
  "How many Nike t-shirts do we have in white color and XS size?",
  "What is the total inventory value of all size S t-shirts?",
  "How much revenue would we make selling all Levis t-shirts after discounts?",
];

function App() {
  const [tables, setTables] = useState<SchemaTable[]>([]);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [traceLoading, setTraceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("answer");
  const [suggestions, setSuggestions] = useState<string[]>(FALLBACK_SUGGESTIONS);

  useEffect(() => {
    getSchema().then(setTables).catch(() => setTables([]));
    getSuggestions()
      .then((r) => setSuggestions(r.suggestions))
      .catch(() => {});
  }, []);

  const handleSubmit = async (question: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setTrace(null);
    try {
      const response = await runQuery(question);
      setResult(response);
      setTab("answer");
      setTraceLoading(true);
      getTrace(response.trace_id)
        .then(setTrace)
        .finally(() => setTraceLoading(false));
      // Fresh, context-aware follow-up suggestions for next time the box is focused —
      // this is what makes the "try asking" list feel alive instead of a fixed list.
      getSuggestions(question, response.answer)
        .then((r) => setSuggestions(r.suggestions))
        .catch(() => {});
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.detail.stage}: ${err.detail.reason}`);
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <main className="app-main">
        <header className="app-header">
          <div>
            <h1>intelligent-query-engine</h1>
            <p className="subtitle">ask the t-shirt inventory a question in plain english</p>
          </div>
          <MenuPanel tables={tables} activeTab={tab} onSelectTab={setTab} />
        </header>

        <QueryForm onSubmit={handleSubmit} loading={loading} suggestions={suggestions} />

        {error && <p className="stage-error-msg top-level-error">{error}</p>}

        <section className="tab-content">
          {tab === "answer" &&
            (result ? <ResultPanel result={result} /> : <p className="empty-note">Ask a question to see the answer here.</p>)}
          {tab === "trace" && <TracePanel trace={trace} loading={traceLoading} />}
          {tab === "eval" && <EvalPanel />}
        </section>
      </main>
    </div>
  );
}

export default App;
