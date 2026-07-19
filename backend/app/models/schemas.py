from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class QueryResponse(BaseModel):
    question: str
    plan: dict
    sql: str
    warnings: list[str]
    columns: list[str]
    rows: list[list]
    answer: str
    trace_id: str


class ErrorResponse(BaseModel):
    stage: str
    reason: str


class TraceSummary(BaseModel):
    id: str
    question: str
    created_at: str
    status: str
    total_duration_ms: float | None


class TraceDetail(TraceSummary):
    stages: list[dict]


class SchemaTableResponse(BaseModel):
    name: str
    columns: list[str]
    create_sql: str


class EvalCaseResultResponse(BaseModel):
    id: str
    question: str
    expected_sql: str
    generated_sql: str | None
    passed: bool
    error: str | None


class EvalReportResponse(BaseModel):
    total: int
    passed: int
    accuracy: float
    cases: list[EvalCaseResultResponse]


class SuggestionsResponse(BaseModel):
    suggestions: list[str]
