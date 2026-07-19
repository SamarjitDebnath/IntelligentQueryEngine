import type {
  ApiErrorDetail,
  EvalReport,
  QueryResponse,
  SchemaTable,
  TraceDetail,
  TraceSummary,
} from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  detail: ApiErrorDetail;

  constructor(detail: ApiErrorDetail) {
    super(`[${detail.stage}] ${detail.reason}`);
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    if (body?.detail) {
      throw new ApiError(body.detail as ApiErrorDetail);
    }
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function runQuery(question: string): Promise<QueryResponse> {
  return request<QueryResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function getSchema(): Promise<SchemaTable[]> {
  return request<SchemaTable[]>("/api/schema");
}

export function listTraces(): Promise<TraceSummary[]> {
  return request<TraceSummary[]>("/api/traces");
}

export function getTrace(traceId: string): Promise<TraceDetail> {
  return request<TraceDetail>(`/api/traces/${traceId}`);
}

export function runEvaluation(): Promise<EvalReport> {
  return request<EvalReport>("/api/eval/run", { method: "POST" });
}

export function getSuggestions(lastQuestion?: string, lastAnswer?: string): Promise<{ suggestions: string[] }> {
  const params = new URLSearchParams();
  if (lastQuestion) params.set("last_question", lastQuestion);
  if (lastAnswer) params.set("last_answer", lastAnswer);
  const query = params.toString();
  return request<{ suggestions: string[] }>(`/api/suggestions${query ? `?${query}` : ""}`);
}
