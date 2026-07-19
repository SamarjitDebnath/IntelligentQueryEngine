"""Generates example questions for the frontend's "try asking" dropdown.

Unlike the fixed few-shot examples (which exist to steer SQL generation), these are
purely UI sugar: a fresh LLM call each time, at higher temperature, optionally nudged by
the user's last question/answer so the suggestions feel like contextual follow-ups
instead of the same static list forever.
"""

import json

from app.core.guardrails import SAFETY_PREAMBLE
from app.core.llm import get_llm
from app.core.schema_introspection import get_schema, render_table_info

FALLBACK_SUGGESTIONS = [
    "How many Nike t-shirts do we have in white color and XS size?",
    "What is the total inventory value of all size S t-shirts?",
    "How much revenue would we make selling all Levis t-shirts after discounts?",
]


def _parse_suggestions(completion: str, count: int) -> list[str]:
    cleaned = completion.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed) and parsed:
            return [s.strip() for s in parsed[:count] if s.strip()]
    except json.JSONDecodeError:
        pass

    # Fallback: the model ignored the "JSON only" instruction — salvage plain lines instead
    # of giving up and falling all the way back to the static list.
    lines = [line.strip(" -*0123456789.\t") for line in completion.splitlines()]
    lines = [line for line in lines if line]
    return lines[:count]


def generate_suggestions(count: int = 3, last_question: str | None = None, last_answer: str | None = None) -> list[str]:
    """Asks the LLM for `count` fresh example questions about the inventory schema.

    Falls back to a static list if the LLM call fails or returns something unusable
    (missing API key, rate limit, empty/malformed response) — this is a nice-to-have
    UI feature and should never be the reason a page fails to load.
    """
    try:
        table_info = render_table_info(get_schema())
        llm = get_llm(temperature=0.9)

        context = ""
        if last_question:
            context = f'The user just asked: "{last_question}"\n'
            if last_answer:
                context += f'They got this answer: "{last_answer}"\n'
            context += (
                "Suggest natural follow-up questions exploring a different angle "
                "(different brand, color, size, discount, or revenue angle) — not a repeat.\n\n"
            )

        prompt = (
            SAFETY_PREAMBLE
            + "You suggest example natural-language questions a user could ask about a "
            "t-shirt store inventory database.\n"
            f"Schema:\n{table_info}\n\n"
            + context
            + f"Suggest {count} short, concrete, varied questions answerable from this schema. "
            "Respond with ONLY a JSON array of strings, no markdown fences, no explanation."
        )
        completion = llm.invoke(prompt)
        suggestions = _parse_suggestions(completion, count)
        return suggestions if suggestions else FALLBACK_SUGGESTIONS[:count]
    except Exception:
        return FALLBACK_SUGGESTIONS[:count]
