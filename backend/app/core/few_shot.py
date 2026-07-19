"""Few-shot example bank for SQL generation, ported from experiment/intelligent_query_engine.ipynb.

Examples are embedded with a local HuggingFace sentence-transformer and stored in Chroma so the
prompt can be augmented, at query time, with the `k` most semantically similar known-good
question/SQL pairs — this is what pushes Gemini toward correct SQL for this schema.
"""

import sqlite3
from decimal import Decimal
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

RAW_EXAMPLES: list[dict[str, str]] = [
    {
        "Question": "How many t-shirts do we have left for Nike in XS size and white color?",
        "SQLQuery": "SELECT SUM(stock_quantity) FROM t_shirts WHERE brand = 'Nike' AND color = 'White' AND size = 'XS'",
    },
    {
        "Question": "How much is the total price of the inventory for all S-size t-shirts?",
        "SQLQuery": "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE size = 'S'",
    },
    {
        "Question": "If we have to sell all the Levi's T-shirts today with discounts applied, how much revenue will our store generate (post discounts)?",
        "SQLQuery": (
            "SELECT SUM(a.total_amount * ((100 - COALESCE(discounts.pct_discount, 0)) / 100)) AS total_revenue "
            "FROM (SELECT SUM(price * stock_quantity) AS total_amount, t_shirt_id FROM t_shirts "
            "WHERE brand = 'Levis' GROUP BY t_shirt_id) a "
            "LEFT JOIN discounts ON a.t_shirt_id = discounts.t_shirt_id"
        ),
    },
    {
        "Question": "If we have to sell all the Levi's T-shirts today without any discount, how much revenue will our store generate?",
        "SQLQuery": "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levis'",
    },
    {
        "Question": "How many white color Levi's t-shirts do I have?",
        "SQLQuery": "SELECT SUM(stock_quantity) FROM t_shirts WHERE brand = 'Levis' AND color = 'White'",
    },
    {
        "Question": "How much sales amount will be generated if we sell all large size t-shirts today in Nike brand after discounts?",
        "SQLQuery": (
            "SELECT SUM(a.total_amount * ((100 - COALESCE(discounts.pct_discount, 0)) / 100)) AS total_revenue "
            "FROM (SELECT SUM(price * stock_quantity) AS total_amount, t_shirt_id FROM t_shirts "
            "WHERE brand = 'Nike' AND size = 'L' GROUP BY t_shirt_id) a "
            "LEFT JOIN discounts ON a.t_shirt_id = discounts.t_shirt_id"
        ),
    },
]

_MYSQL_STYLE_PREFIX = """You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause. You can order the results to return the most informative data in the database.
Never query for all columns from a table. Only query the columns needed to answer the question. Pay attention to use only the column names you can see in the tables below, and to which column belongs to which table.
Pay attention to use date('now') to get the current date, if the question involves "today".

Use the following format:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here
"""

_PROMPT_SUFFIX = """Only use the following tables:
{table_info}

Question: {input}"""

_EXAMPLE_PROMPT = PromptTemplate(
    input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],
    template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}",
)


def _resolve_example_answers(examples: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Runs each example's SQL against the seeded SQLite DB to attach a real Answer/SQLResult."""
    connection = sqlite3.connect(settings.sqlite_path)
    resolved = []
    try:
        for idx, example in enumerate(examples, start=1):
            answer: Any = "No result"
            result = "Result of the SQL query"
            try:
                row = connection.execute(example["SQLQuery"]).fetchone()
                if row and row[0] is not None:
                    value = row[0]
                    answer = int(value) if isinstance(value, Decimal) and value == value.to_integral_value() else value
            except sqlite3.Error as exc:
                result = f"Error executing query: {exc}"

            resolved.append(
                {
                    "id": idx,
                    "Question": example["Question"],
                    "SQLQuery": example["SQLQuery"],
                    "SQLResult": result,
                    "Answer": answer,
                }
            )
    finally:
        connection.close()
    return resolved


@lru_cache(maxsize=1)
def build_few_shot_prompt() -> FewShotPromptTemplate:
    examples = _resolve_example_answers(RAW_EXAMPLES)
    to_vectorize = [
        " ".join(str(v) for k, v in example.items() if k != "id") for example in examples
    ]

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vectorstore = Chroma.from_texts(
        to_vectorize,
        embeddings,
        metadatas=examples,
        persist_directory=str(settings.chroma_persist_dir),
        collection_name="iqe_few_shot_examples",
    )
    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=min(settings.few_shot_examples_k, len(examples)),
        # Restrict similarity search to the question only — otherwise the selector
        # concatenates *all* FewShotPromptTemplate.format() kwargs (including the
        # int `top_k`) via `" ".join(...)`, which raises a TypeError.
        input_keys=["input"],
    )

    return FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=_EXAMPLE_PROMPT,
        prefix=_MYSQL_STYLE_PREFIX,
        suffix=_PROMPT_SUFFIX,
        input_variables=["input", "table_info", "top_k"],
    )
