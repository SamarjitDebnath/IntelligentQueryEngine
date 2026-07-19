"""Lightweight, dependency-free observability for the query pipeline.

Every request gets a Trace made up of Stages (plan, generate_sql, validate_sql, execute_sql,
synthesize_answer). Traces are kept in-memory (most recent 200) and exposed via
GET /api/traces and /api/traces/{id} so the frontend can show exactly what the pipeline did
and how long each step took, without wiring up an external tracing backend.

If LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY are set in the environment, LangChain's
own calls (LLM invocations) will *additionally* be traced to LangSmith automatically — this
in-memory tracer works standalone either way.
"""

import time
import uuid
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Iterator


@dataclass
class Stage:
    name: str
    status: str = "running"
    input: Any = None
    output: Any = None
    error: str | None = None
    started_at: float = field(default_factory=time.perf_counter)
    duration_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class Trace:
    id: str
    question: str
    created_at: str
    stages: list[Stage] = field(default_factory=list)
    status: str = "running"
    total_duration_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "created_at": self.created_at,
            "status": self.status,
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
        }


class Tracer:
    def __init__(self, max_traces: int = 200):
        self._traces: deque[Trace] = deque(maxlen=max_traces)
        self._by_id: dict[str, Trace] = {}
        self._lock = Lock()

    def start_trace(self, question: str) -> Trace:
        trace = Trace(id=str(uuid.uuid4()), question=question, created_at=datetime.now(timezone.utc).isoformat())
        with self._lock:
            self._traces.append(trace)
            self._by_id[trace.id] = trace
        return trace

    def finish_trace(self, trace: Trace, status: str, total_duration_ms: float) -> None:
        trace.status = status
        trace.total_duration_ms = total_duration_ms

    @contextmanager
    def stage(self, trace: Trace, name: str, input: Any = None) -> Iterator[Stage]:
        stage = Stage(name=name, input=input)
        trace.stages.append(stage)
        start = time.perf_counter()
        try:
            yield stage
            stage.status = "ok"
        except Exception as exc:
            stage.status = "error"
            stage.error = str(exc)
            raise
        finally:
            stage.duration_ms = round((time.perf_counter() - start) * 1000, 2)

    def recent(self, limit: int = 50) -> list[Trace]:
        with self._lock:
            return list(self._traces)[-limit:][::-1]

    def get(self, trace_id: str) -> Trace | None:
        with self._lock:
            return self._by_id.get(trace_id)


tracer = Tracer()
