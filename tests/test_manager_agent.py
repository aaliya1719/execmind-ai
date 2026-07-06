"""Comprehensive tests for the Manager Agent (app/agents/manager_agent.py).

Tests cover successful orchestration, report structure validation,
empty/invalid input handling, business health generation rules,
and end-to-end pipeline execution.
"""

import sys
import os
import pandas as pd

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.manager_agent import build_report



# ------------------------------------------------------------------ #
# Helper Mock Data Builders                                          #
# ------------------------------------------------------------------ #

def _make_healthy_df() -> pd.DataFrame:
    """Return a dataset representing a healthy business.

    Stable/growing trend, distributed products, no cancellation issues.
    """
    return pd.DataFrame({
        "Order Number": [100, 101, 102, 103, 104, 105, 106, 107],
        "Sales": [1000.0, 1200.0, 1100.0, 1300.0, 1250.0, 1400.0, 1350.0, 1500.0],
        "Product Code": ["A", "B", "C", "D", "A", "B", "C", "D"],
        "Country": ["USA", "UK", "Canada", "Germany", "USA", "UK", "Canada", "Germany"],
        "Customer Name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi"],
        "Quantity Ordered": [5, 4, 3, 5, 4, 3, 5, 4],
        "Order Date": [
            "2026-01-01", "2026-01-15",
            "2026-02-01", "2026-02-15",
            "2026-03-01", "2026-03-15",
            "2026-04-01", "2026-04-15"
        ],
        "Status": ["Shipped"] * 8
    })


def _make_moderate_df() -> pd.DataFrame:
    """Return a dataset representing a moderate business.

    Declining trend (Jan=5000, Feb=3000, Mar=1000) or slight risks.
    """
    return pd.DataFrame({
        "Order Number": [200, 201, 202, 203, 204],
        "Sales": [3000.0, 2000.0, 1500.0, 1000.0, 500.0],
        "Product Code": ["PROD_X", "PROD_Y", "PROD_Z", "PROD_W", "PROD_X"],
        "Country": ["USA", "USA", "Canada", "UK", "Germany"],
        "Customer Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "Quantity Ordered": [2, 2, 1, 1, 1],
        "Order Date": [
            "2026-01-10", "2026-01-20",
            "2026-02-10", "2026-02-20",
            "2026-03-05"
        ],
        "Status": ["Shipped", "Shipped", "Shipped", "Shipped", "Shipped"]
    })


def _make_critical_df() -> pd.DataFrame:
    """Return a dataset representing a critical business.

    High risks (high cancellation, high product concentration, high geo concentration).
    """
    return pd.DataFrame({
        "Order Number": [300, 301, 302, 303, 304, 305],
        # 10000.0 is ~87% of total revenue (11450.0) -> Critical Product Concentration
        # USA has all but Canada -> High Geo Concentration
        # 2 Cancelled out of 6 -> ~33% High cancellation
        "Sales": [10000.0, 500.0, 300.0, 400.0, 150.0, 100.0],
        "Product Code": ["PROD_MAX", "PROD_MIN", "PROD_MIN", "PROD_MIN", "PROD_MIN", "PROD_MIN"],
        "Country": ["USA", "USA", "USA", "USA", "USA", "Canada"],
        "Customer Name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "Quantity Ordered": [10, 1, 1, 1, 1, 1],
        "Order Date": [
            "2026-01-05", "2026-01-15",
            "2026-02-05", "2026-02-15",
            "2026-03-05", "2026-03-15"
        ],
        "Status": ["Shipped", "Cancelled", "Shipped", "Cancelled", "Shipped", "Shipped"]
    })


# ------------------------------------------------------------------ #
# Unit / Integration Tests                                           #
# ------------------------------------------------------------------ #

def test_report_structure():
    """Verify that build_report returns all specified output keys and correct formats."""
    df = _make_healthy_df()
    report = build_report(df)

    expected_keys = {
        "executive_summary",
        "business_health",
        "sales_insights",
        "marketing_recommendations",
        "financial_assessment",
        "overall_risks",
        "top_priorities",
        "recommended_next_steps"
    }

    assert expected_keys == set(report.keys()), f"Missing keys in report. Got: {list(report.keys())}"
    assert isinstance(report["executive_summary"], list)
    assert isinstance(report["business_health"], str)
    assert isinstance(report["sales_insights"], dict)
    assert isinstance(report["marketing_recommendations"], dict)
    assert isinstance(report["financial_assessment"], dict)
    assert isinstance(report["overall_risks"], list)
    assert isinstance(report["top_priorities"], list)
    assert isinstance(report["recommended_next_steps"], list)

    print("Structure validation test passed successfully.")


def test_business_health_healthy():
    df = _make_healthy_df()
    report = build_report(df)
    print(f"Healthy Data - Business Health: {report['business_health']}")
    assert report["business_health"] == "Healthy"


def test_business_health_moderate():
    df = _make_moderate_df()
    report = build_report(df)
    print(f"Moderate Data - Business Health: {report['business_health']}")
    # Declining trend should trigger Moderate health (or Critical if high risks present)
    assert report["business_health"] == "Moderate"


def test_business_health_critical():
    df = _make_critical_df()
    report = build_report(df)
    print(f"Critical Data - Business Health: {report['business_health']}")
    # High product concentration + high geo concentration + high cancellations -> Critical
    assert report["business_health"] == "Critical"


def test_business_health_score_is_dynamic():
    healthy = build_report(_make_healthy_df())
    moderate = build_report(_make_moderate_df())
    critical = build_report(_make_critical_df())

    healthy_score = int(healthy["financial_assessment"]["business_health_score"])
    moderate_score = int(moderate["financial_assessment"]["business_health_score"])
    critical_score = int(critical["financial_assessment"]["business_health_score"])

    print(
        f"Health scores: healthy={healthy_score}, moderate={moderate_score}, critical={critical_score}"
    )

    assert 0 <= critical_score <= 100
    assert 0 <= moderate_score <= 100
    assert 0 <= healthy_score <= 100
    assert healthy_score > moderate_score > critical_score


def test_invalid_inputs():
    """Verify that build_report raises ValueError on invalid/empty data."""
    # Test None input
    try:
        build_report(None)
        assert False, "Expected ValueError when input is None"
    except ValueError as exc:
        assert "cannot be None" in str(exc) or "must be a" in str(exc)

    # Test non-DataFrame input
    try:
        build_report("not a dataframe")
        assert False, "Expected ValueError when input is not a DataFrame"
    except ValueError as exc:
        assert "must be a pandas DataFrame" in str(exc) or "cannot be" in str(exc)

    # Test empty DataFrame
    empty_df = pd.DataFrame()
    try:
        build_report(empty_df)
        assert False, "Expected ValueError when DataFrame is empty"
    except ValueError as exc:
        assert "is empty" in str(exc) or "empty or None" in str(exc)

    print("Invalid input validation tests passed successfully.")



def test_top_priorities_generation():
    """Verify top priorities length and actionability."""
    df = _make_critical_df()
    report = build_report(df)
    priorities = report["top_priorities"]
    print(f"Critical priorities ({len(priorities)}): {priorities}")
    assert len(priorities) >= 3 and len(priorities) <= 5
    # Ensure they suggest mitigating risks or launching promotions
    assert any("Mitigate" in p or "Establish" in p or "Ensure" in p or "campaign" in p.lower() for p in priorities)


def test_recommended_next_steps():
    df = _make_healthy_df()
    report = build_report(df)
    next_steps = report["recommended_next_steps"]
    print(f"Next steps: {next_steps}")
    assert len(next_steps) >= 3


def test_end_to_end_pipeline():
    """End-to-end sanity checks on output value consistency."""
    df = _make_healthy_df()
    report = build_report(df)

    # Sales KPI checks
    sales = report["sales_insights"]
    assert sales["total_sales"] == 10100.0
    assert sales["total_orders"] == 8
    assert sales["average_order_value"] == 1262.5

    # Marketing Recommendation checks
    mkt = report["marketing_recommendations"]
    assert len(mkt["suggested_promotions"]) > 0

    # Financial Assessment checks
    fin = report["financial_assessment"]
    assert fin["financial_kpis"]["total_revenue"] == 10100.0
    assert fin["revenue_health"]["status"] == "Growing"


    print("End-to-end pipeline test passed successfully.")


# ------------------------------------------------------------------ #
# Runner                                                             #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    tests = [
        test_report_structure,
        test_business_health_healthy,
        test_business_health_moderate,
        test_business_health_critical,
        test_business_health_score_is_dynamic,
        test_invalid_inputs,
        test_top_priorities_generation,
        test_recommended_next_steps,
        test_end_to_end_pipeline
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS  {test_fn.__name__}")
            passed += 1
        except Exception as exc:
            import traceback
            print(f"  FAIL  {test_fn.__name__}: {exc}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.")
    if failed:
        raise SystemExit(1)
