"""Deterministic (no-LLM) attester for the revenue Attested Computation.

Takes a run receipt and returns a verdict. Runs consumer-side; this file is a
first-class reference concept in the bundle (OKF v0.2 §6.3, §10.2). Runtime
receipts are never stored in the bundle.
"""

EXPECTED_SQL = (
    "SELECT SUM(total_usd) AS revenue\n"
    "FROM sales.orders\n"
    "WHERE EXTRACT(YEAR FROM placed_at) = @year"
)


def attest(receipt: dict) -> dict:
    """Confirm the sanctioned computation ran, unmodified."""
    ok = receipt.get("executed_sql", "").strip() == EXPECTED_SQL.strip()
    return {"verdict": "pass" if ok else "fail", "job_id": receipt.get("job_id")}
