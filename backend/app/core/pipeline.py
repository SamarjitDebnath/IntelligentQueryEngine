"""The NL -> SQL query pipeline: plan -> generate SQL -> validate -> execute -> answer.

Each stage is wrapped in a tracer.stage(...) span so the full reasoning trail (including
guardrail warnings/violations and timings) is captured and returned to the caller instead
of being hidden inside an opaque chain.
"""

import json
import re
import sqlite3
import time
from dataclasses import dataclass, field

from app.config import settings
from app.core.few_shot import build_few_shot_prompt
from app.core.guardrails import (
    SAFETY_PREAMBLE,
    GuardrailViolation,
    PromptInjectionViolation,
    check_question_safety,
    redact_secrets,
    redact_secrets_deep,
    validate_and_harden_sql,
)
from app.core.llm import get_llm
from app.core.schema_introspection import get_schema, render_table_info
from app.core.tracing import Trace, tracer

_SQL_LINE_RE = re.compile(r"SQLQuery\s*:\s*(.*?)(?:\nSQLResult\s*:|\nAnswer\s*:|$)", re.IGNORECASE | re.DOTALL)
_SAFETY_PREAMBLE = SAFETY_PREAMBLE


class PipelineError(Exception):
    def __init__(self, stage: str, reason: str):
        self.stage = stage
        self.reason = reason
        super().__init__(f"[{stage}] {reason}")


@dataclass
class QueryResult:
    question: str
    plan: dict
    sql: str
    warnings: list[str]
    columns: list[str]
    rows: list[list]
    answer: str
    trace_id: str
    trace: dict = field(default_factory=dict)


def _extract_sql(raw_completion: str) -> str:
    match = _SQL_LINE_RE.search(raw_completion)
    candidate = match.group(1) if match else raw_completion
    candidate = candidate.strip().strip("`")
    if candidate.lower().startswith("sql"):
        candidate = candidate[3:].strip()
    return candidate.strip()


def _plan(question: str, table_info: str) -> dict:
    llm = get_llm(temperature=0.0)
    prompt = (
        _SAFETY_PREAMBLE
        + "You are planning how to answer a question about a t-shirt store inventory database.\n"
        f"Schema:\n{table_info}\n\n"
        f'Question: "{question}"\n\n'
        "Respond with ONLY a compact JSON object (no markdown fences) with keys:\n"
        '  "tables": list of table names you will need,\n'
        '  "approach": one short sentence describing the calculation/filters needed.'
    )
    completion = llm.invoke(prompt)
    try:
        cleaned = completion.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        plan = json.loads(cleaned)
        if not isinstance(plan, dict):
            raise ValueError("plan is not a JSON object")
        return plan
    except (json.JSONDecodeError, ValueError):
        return {"tables": [], "approach": completion.strip()}


def _generate_sql(question: str, table_info: str) -> str:
    llm = get_llm(temperature=0.0)
    few_shot_prompt = build_few_shot_prompt()
    rendered = _SAFETY_PREAMBLE + few_shot_prompt.format(input=question, table_info=table_info, top_k=5)
    completion = llm.invoke(rendered)
    return _extract_sql(completion)


def _fix_sql(question: str, table_info: str, bad_sql: str, reason: str) -> str:
    llm = get_llm(temperature=0.0)
    prompt = (
        _SAFETY_PREAMBLE
        + "The following SQLite query was rejected by a validator.\n\n"
        f"Schema:\n{table_info}\n\n"
        f'Question: "{question}"\n'
        f"Rejected SQLQuery: {bad_sql}\n"
        f"Rejection reason: {reason}\n\n"
        "Write a corrected SQLite SELECT query that answers the question and respects the schema. "
        "Respond with ONLY the SQL, no explanation, no markdown fences."
    )
    completion = llm.invoke(prompt)
    return _extract_sql(completion)


def _execute(sql: str, row_cap: int) -> tuple[list[str], list[list]]:
    connection = sqlite3.connect(f"file:{settings.sqlite_path}?mode=ro", uri=True)
    try:
        cursor = connection.execute(sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchmany(row_cap)]
        return columns, rows
    finally:
        connection.close()


def _synthesize_answer(question: str, sql: str, columns: list[str], rows: list[list]) -> str:
    llm = get_llm(temperature=0.2)
    preview = rows[:10]
    prompt = (
        _SAFETY_PREAMBLE
        + f'Question: "{question}"\n'
        f"SQLQuery: {sql}\n"
        f"SQLResult columns: {columns}\n"
        f"SQLResult rows (up to 10 shown): {preview}\n\n"
        "Give a short, direct, natural-language answer to the question using only this result. "
        "If the result is empty, say so plainly."
    )
    return llm.invoke(prompt).strip()


def run_query(question: str, row_cap: int = 100) -> QueryResult:
    trace: Trace = tracer.start_trace(question)
    start = time.perf_counter()
    schema = get_schema()
    table_info = render_table_info(schema)

    try:
        with tracer.stage(trace, "input_safety", input={"question": question}) as stage:
            try:
                check_question_safety(question)
            except PromptInjectionViolation as violation:
                raise PipelineError("input_safety", violation.reason) from violation
            stage.output = {"passed": True}

        with tracer.stage(trace, "plan", input={"question": question}) as stage:
            plan = _plan(question, table_info)
            stage.output = plan

        with tracer.stage(trace, "generate_sql", input={"plan": plan}) as stage:
            sql = _generate_sql(question, table_info)
            stage.output = {"sql": sql}

        warnings: list[str] = []
        with tracer.stage(trace, "validate_sql", input={"sql": sql}) as stage:
            try:
                result = validate_and_harden_sql(sql)
            except GuardrailViolation as first_violation:
                stage.output = {"first_attempt_rejected": first_violation.reason}
                sql = _fix_sql(question, table_info, sql, first_violation.reason)
                try:
                    result = validate_and_harden_sql(sql)
                except GuardrailViolation as second_violation:
                    raise PipelineError("validate_sql", second_violation.reason) from second_violation
            sql = result.sql
            warnings = result.warnings
            stage.output = {**(stage.output or {}), "hardened_sql": sql, "warnings": warnings}

        with tracer.stage(trace, "execute_sql", input={"sql": sql}) as stage:
            columns, rows = _execute(sql, row_cap)
            stage.output = {"row_count": len(rows), "columns": columns}

        with tracer.stage(trace, "synthesize_answer", input={"row_count": len(rows)}) as stage:
            answer = _synthesize_answer(question, sql, columns, rows)
            stage.output = {"answer": answer}

        tracer.finish_trace(trace, "ok", round((time.perf_counter() - start) * 1000, 2))
        return QueryResult(
            question=question,
            plan=redact_secrets_deep(plan),
            sql=redact_secrets(sql),
            warnings=warnings,
            columns=columns,
            rows=rows,
            answer=redact_secrets(answer),
            trace_id=trace.id,
            trace=redact_secrets_deep(trace.to_dict()),
        )
    except PipelineError:
        tracer.finish_trace(trace, "error", round((time.perf_counter() - start) * 1000, 2))
        raise
    except Exception as exc:
        tracer.finish_trace(trace, "error", round((time.perf_counter() - start) * 1000, 2))
        raise PipelineError("unknown", str(exc)) from exc
