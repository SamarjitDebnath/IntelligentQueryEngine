"""Runs the validation dataset through the real pipeline and scores execution accuracy:
does the LLM-generated SQL return the same result set as a hand-written gold query?

CLI:  uv run python -m app.eval.runner
API:  POST /api/eval/run
"""

import math
from dataclasses import dataclass, field

from app.core.pipeline import PipelineError, _execute, run_query
from app.eval.dataset import EVAL_CASES, EvalCase


@dataclass
class EvalCaseResult:
    id: str
    question: str
    expected_sql: str
    generated_sql: str | None
    passed: bool
    error: str | None = None


@dataclass
class EvalReport:
    total: int
    passed: int
    accuracy: float
    cases: list[EvalCaseResult] = field(default_factory=list)


def _cell_equal(a, b, rel_tol: float = 1e-4) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=1e-6)
    return a == b


def _rows_match(expected: list[list], actual: list[list]) -> bool:
    if len(expected) != len(actual):
        return False
    remaining = list(actual)
    for expected_row in expected:
        match_idx = next(
            (i for i, row in enumerate(remaining) if len(row) == len(expected_row) and all(_cell_equal(a, b) for a, b in zip(expected_row, row))),
            None,
        )
        if match_idx is None:
            return False
        remaining.pop(match_idx)
    return True


def _run_case(case: EvalCase) -> EvalCaseResult:
    try:
        _, expected_rows = _execute(case.expected_sql, row_cap=1000)
    except Exception as exc:  # gold SQL itself failed — dataset bug, not model failure
        return EvalCaseResult(case.id, case.question, case.expected_sql, None, False, f"Gold SQL failed: {exc}")

    try:
        result = run_query(case.question)
    except PipelineError as exc:
        return EvalCaseResult(case.id, case.question, case.expected_sql, None, False, f"[{exc.stage}] {exc.reason}")

    passed = _rows_match(expected_rows, result.rows)
    return EvalCaseResult(case.id, case.question, case.expected_sql, result.sql, passed)


def run_evaluation(cases: list[EvalCase] | None = None) -> EvalReport:
    cases = cases if cases is not None else EVAL_CASES
    results = [_run_case(case) for case in cases]
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    return EvalReport(total=total, passed=passed, accuracy=round(passed / total, 3) if total else 0.0, cases=results)


if __name__ == "__main__":
    report = run_evaluation()
    print(f"\nValidation results: {report.passed}/{report.total} passed ({report.accuracy:.1%})\n")
    for case in report.cases:
        status = "PASS" if case.passed else "FAIL"
        print(f"[{status}] {case.id}: {case.question}")
        if not case.passed:
            print(f"       expected_sql = {case.expected_sql}")
            print(f"       generated_sql = {case.generated_sql}")
            if case.error:
                print(f"       error = {case.error}")
