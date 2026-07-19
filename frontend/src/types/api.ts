export interface QueryPlan {
  tables?: string[];
  approach?: string;
  [key: string]: unknown;
}

export interface QueryResponse {
  question: string;
  plan: QueryPlan;
  sql: string;
  warnings: string[];
  columns: string[];
  rows: unknown[][];
  answer: string;
  trace_id: string;
}

export interface ApiErrorDetail {
  stage: string;
  reason: string;
}

export interface TraceStage {
  name: string;
  status: "running" | "ok" | "error";
  input: unknown;
  output: unknown;
  error: string | null;
  duration_ms: number | null;
}

export interface TraceSummary {
  id: string;
  question: string;
  created_at: string;
  status: string;
  total_duration_ms: number | null;
}

export interface TraceDetail extends TraceSummary {
  stages: TraceStage[];
}

export interface SchemaTable {
  name: string;
  columns: string[];
  create_sql: string;
}

export interface EvalCaseResult {
  id: string;
  question: string;
  expected_sql: string;
  generated_sql: string | null;
  passed: boolean;
  error: string | null;
}

export interface EvalReport {
  total: number;
  passed: number;
  accuracy: number;
  cases: EvalCaseResult[];
}
