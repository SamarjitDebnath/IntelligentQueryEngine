from fastapi import APIRouter, HTTPException

from app.core.guardrails import redact_secrets_deep
from app.core.pipeline import PipelineError, run_query
from app.core.schema_introspection import get_schema
from app.core.suggestions import generate_suggestions
from app.core.tracing import tracer
from app.eval.runner import run_evaluation
from app.models.schemas import (
    EvalReportResponse,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    SchemaTableResponse,
    SuggestionsResponse,
    TraceDetail,
    TraceSummary,
)

router = APIRouter(prefix="/api", tags=["query-engine"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/schema", response_model=list[SchemaTableResponse])
def schema() -> list[SchemaTableResponse]:
    return [
        SchemaTableResponse(name=t.name, columns=t.columns, create_sql=t.create_sql)
        for t in get_schema()
    ]


@router.get("/suggestions", response_model=SuggestionsResponse)
def suggestions(last_question: str | None = None, last_answer: str | None = None) -> SuggestionsResponse:
    return SuggestionsResponse(suggestions=generate_suggestions(last_question=last_question, last_answer=last_answer))


@router.post("/query", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
def query(request: QueryRequest) -> QueryResponse:
    try:
        result = run_query(request.question)
    except PipelineError as exc:
        raise HTTPException(status_code=400, detail={"stage": exc.stage, "reason": exc.reason}) from exc

    return QueryResponse(
        question=result.question,
        plan=result.plan,
        sql=result.sql,
        warnings=result.warnings,
        columns=result.columns,
        rows=result.rows,
        answer=result.answer,
        trace_id=result.trace_id,
    )


@router.get("/traces", response_model=list[TraceSummary])
def list_traces(limit: int = 50) -> list[TraceSummary]:
    return [
        TraceSummary(
            id=t.id, question=t.question, created_at=t.created_at, status=t.status, total_duration_ms=t.total_duration_ms
        )
        for t in tracer.recent(limit=limit)
    ]


@router.get("/traces/{trace_id}", response_model=TraceDetail, responses={404: {"model": ErrorResponse}})
def get_trace(trace_id: str) -> TraceDetail:
    trace = tracer.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail={"stage": "traces", "reason": f"No trace with id {trace_id}"})
    data = redact_secrets_deep(trace.to_dict())
    return TraceDetail(**data)


@router.post("/eval/run", response_model=EvalReportResponse)
def eval_run() -> EvalReportResponse:
    report = run_evaluation()
    return EvalReportResponse(
        total=report.total,
        passed=report.passed,
        accuracy=report.accuracy,
        cases=[
            {
                "id": c.id,
                "question": c.question,
                "expected_sql": c.expected_sql,
                "generated_sql": c.generated_sql,
                "passed": c.passed,
                "error": c.error,
            }
            for c in report.cases
        ],
    )
