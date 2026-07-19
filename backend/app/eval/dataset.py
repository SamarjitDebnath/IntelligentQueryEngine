"""Validation dataset for the NL -> SQL pipeline.

Distinct from the few-shot examples in app/core/few_shot.py (those are shown to the LLM as
in-context examples; these are held out to *measure* generation quality via execution
accuracy — the generated SQL's result set is compared against the gold SQL's result set).
"""

from dataclasses import dataclass


@dataclass
class EvalCase:
    id: str
    question: str
    expected_sql: str
    tags: list[str]


EVAL_CASES: list[EvalCase] = [
    EvalCase(
        id="stock-single-filter",
        question="How many Adidas t-shirts in size L do we have in stock?",
        expected_sql="SELECT SUM(stock_quantity) FROM t_shirts WHERE brand = 'Adidas' AND size = 'L'",
        tags=["aggregation", "filter"],
    ),
    EvalCase(
        id="inventory-value-by-color",
        question="What is the total inventory value of all black t-shirts?",
        expected_sql="SELECT SUM(price * stock_quantity) FROM t_shirts WHERE color = 'Black'",
        tags=["aggregation", "multiply"],
    ),
    EvalCase(
        id="revenue-with-discount",
        question="If we sold every Puma t-shirt today with discounts applied, how much revenue would we make?",
        expected_sql=(
            "SELECT SUM(a.total_amount * ((100 - COALESCE(discounts.pct_discount, 0)) / 100)) AS total_revenue "
            "FROM (SELECT SUM(price * stock_quantity) AS total_amount, t_shirt_id FROM t_shirts "
            "WHERE brand = 'Puma' GROUP BY t_shirt_id) a "
            "LEFT JOIN discounts ON a.t_shirt_id = discounts.t_shirt_id"
        ),
        tags=["join", "discount", "revenue"],
    ),
    EvalCase(
        id="count-distinct-brand",
        question="How many different t-shirt brands do we stock?",
        expected_sql="SELECT COUNT(DISTINCT brand) FROM t_shirts",
        tags=["distinct", "count"],
    ),
    EvalCase(
        id="max-price-per-brand",
        question="What is the highest priced Nike t-shirt?",
        expected_sql="SELECT MAX(price) FROM t_shirts WHERE brand = 'Nike'",
        tags=["aggregation", "max"],
    ),
    EvalCase(
        id="discount-count",
        question="How many t-shirts currently have a discount applied?",
        expected_sql="SELECT COUNT(*) FROM discounts",
        tags=["count"],
    ),
]
