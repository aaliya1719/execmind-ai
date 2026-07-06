"""Comprehensive tests for the Finance Agent (app/agents/finance_agent.py).

Tests cover DataFrame mode, dictionary mode, forecast generation,
risk detection, KPI generation, and executive summary generation.
"""

import sys
import os
import pandas as pd

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.finance_agent import (
    estimate_financial_impact,
    _assess_revenue_health,
    _generate_forecast,
)


# ------------------------------------------------------------------ #
# Shared fixtures                                                     #
# ------------------------------------------------------------------ #

def _make_mock_df() -> pd.DataFrame:
    """Return a rich mock DataFrame covering all optional columns."""
    return pd.DataFrame({
        "Order Number":       [1001, 1001, 1002, 1002, 1003, 1004, 1005],
        "Sales":              [3000.0, 1500.0, 500.0, 200.0, 8000.0, 4000.0, 300.0],
        "Quantity Ordered":   [3, 2, 1, 1, 5, 4, 1],
        "Product Code":       ["PROD_A", "PROD_B", "PROD_C", "PROD_D", "PROD_A", "PROD_B", "PROD_D"],
        "Country":            ["USA", "USA", "Canada", "Canada", "USA", "UK", "UK"],
        "Customer Name":      ["Alice", "Alice", "Bob", "Bob", "Charlie", "Diana", "Eve"],
        "Order Date":         [
            "2026-01-10", "2026-01-10",
            "2026-01-20", "2026-01-20",
            "2026-02-05", "2026-02-15",
            "2026-03-01",
        ],
        "Status": ["Shipped", "Shipped", "Cancelled", "Cancelled", "Shipped", "Shipped", "Shipped"],
    })


def _make_mock_sales_insights() -> dict:
    """Return a pre-computed sales insights dictionary."""
    return {
        "total_sales": 17500.0,
        "total_orders": 10,
        "average_order_value": 1750.0,
        "monthly_sales_trend": {
            "2026-01": 5200.0,
            "2026-02": 12000.0,
            "2026-03": 300.0,
        },
        "top_products_by_revenue": {
            "PROD_A": 11000.0,
            "PROD_B": 5500.0,
            "PROD_C": 700.0,
            "PROD_D": 300.0,
        },
        "top_countries_by_revenue": {
            "USA": 15000.0,
            "UK": 2000.0,
            "Canada": 500.0,
        },
        "deal_size_distribution": {"Large": 3, "Medium": 4, "Small": 3},
        "order_status_summary": {"Shipped": 8, "Cancelled": 2},
    }


# ------------------------------------------------------------------ #
# Helper unit tests                                                   #
# ------------------------------------------------------------------ #

def test_revenue_health_growing():
    trend = {"2026-01": 1000.0, "2026-02": 1200.0, "2026-03": 1100.0, "2026-04": 1500.0}
    status, explanation = _assess_revenue_health(trend)
    print(f"Revenue Health (Growing): status={status}")
    assert status == "Growing", f"Expected Growing, got {status}"


def test_revenue_health_declining():
    trend = {"2026-01": 5000.0, "2026-02": 4000.0, "2026-03": 500.0, "2026-04": 400.0}
    status, explanation = _assess_revenue_health(trend)
    print(f"Revenue Health (Declining): status={status}")
    assert status == "Declining", f"Expected Declining, got {status}"


def test_revenue_health_stable():
    trend = {"2026-01": 1000.0, "2026-02": 1020.0}
    status, explanation = _assess_revenue_health(trend)
    print(f"Revenue Health (Stable): status={status}")
    assert status == "Stable", f"Expected Stable, got {status}"


def test_revenue_health_single_period():
    """Single period must fall back to Stable with an explanation."""
    trend = {"2026-01": 1000.0}
    status, explanation = _assess_revenue_health(trend)
    print(f"Revenue Health (Single period): status={status}")
    assert status == "Stable"
    assert "Insufficient" in explanation


def test_revenue_health_empty():
    status, explanation = _assess_revenue_health({})
    print(f"Revenue Health (Empty): status={status}")
    assert status == "Stable"


# ------------------------------------------------------------------ #
# Forecast tests                                                      #
# ------------------------------------------------------------------ #

def test_forecast_three_periods():
    """3-period WMA: weights [1, 2, 3] → (1000*1 + 2000*2 + 3000*3) / 6 = 2333.33"""
    trend = {"2026-01": 1000.0, "2026-02": 2000.0, "2026-03": 3000.0}
    forecast = _generate_forecast(trend)
    expected = round((1000 * 1 + 2000 * 2 + 3000 * 3) / 6, 2)
    print(f"Forecast (3 periods): projected={forecast['projected_revenue']} expected={expected}")
    assert forecast["projected_revenue"] == expected
    assert forecast["confidence"] == "Low"
    assert "Weighted Moving Average" in forecast["method"]


def test_forecast_six_periods():
    """Six periods → confidence should be Medium."""
    trend = {f"2026-{i:02d}": float(i * 1000) for i in range(1, 7)}
    forecast = _generate_forecast(trend)
    print(f"Forecast (6 periods): confidence={forecast['confidence']}")
    assert forecast["confidence"] == "Medium"


def test_forecast_two_periods():
    trend = {"2026-01": 2000.0, "2026-02": 4000.0}
    forecast = _generate_forecast(trend)
    expected = round((4000 * 2 + 2000) / 3, 2)
    print(f"Forecast (2 periods): projected={forecast['projected_revenue']} expected={expected}")
    assert forecast["projected_revenue"] == expected
    assert forecast["confidence"] == "Low"


def test_forecast_one_period():
    trend = {"2026-01": 5000.0}
    forecast = _generate_forecast(trend)
    print(f"Forecast (1 period): projected={forecast['projected_revenue']}")
    assert forecast["projected_revenue"] == 5000.0
    assert forecast["confidence"] == "Very Low"


def test_forecast_empty():
    forecast = _generate_forecast({})
    print(f"Forecast (empty): projected={forecast['projected_revenue']}")
    assert forecast["projected_revenue"] == 0.0
    assert forecast["confidence"] == "Very Low"


# ------------------------------------------------------------------ #
# DataFrame mode tests                                                #
# ------------------------------------------------------------------ #

def test_dataframe_mode_structure():
    """Verify all required top-level keys are present in DataFrame mode."""
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    required_keys = {
        "revenue_health",
        "financial_kpis",
        "financial_risks",
        "profitability_observations",
        "revenue_forecast",
        "executive_financial_summary",
    }
    print(f"DataFrame mode keys: {set(result.keys())}")
    assert required_keys == set(result.keys())


def test_dataframe_mode_kpis():
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    kpis = result["financial_kpis"]
    print(f"KPIs: {kpis}")

    assert kpis["total_revenue"] > 0
    assert kpis["total_orders"] > 0
    assert kpis["average_order_value"] > 0
    assert "peak_monthly_revenue" in kpis
    assert "trough_monthly_revenue" in kpis
    assert kpis["peak_monthly_revenue"] >= kpis["trough_monthly_revenue"]

    # Average items per order should be computed (Quantity Ordered column present)
    assert "average_items_per_order" in kpis
    assert kpis["average_items_per_order"] > 0

    # Revenue per customer should be computed (Customer Name column present)
    assert "revenue_per_customer" in kpis
    assert kpis["revenue_per_customer"] > 0


def test_dataframe_mode_risks():
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    risks = result["financial_risks"]
    risk_types = [r["risk_type"] for r in risks]
    print(f"Risks detected: {risk_types}")

    # PROD_A total = 3000 + 8000 = 11000 out of 17500 ≈ 62.9% → Critical Product Concentration
    assert any("Product Concentration" in rt for rt in risk_types)

    # USA total = 3000 + 1500 + 8000 = 12500 out of 17500 ≈ 71.4% → Critical Geographic
    assert any("Geographic Concentration" in rt for rt in risk_types)

    # 2 Cancelled out of 7 records ≈ 28.6% → High Revenue Leakage
    assert any("Leakage" in rt for rt in risk_types)

    # Ensure every risk has required keys
    for risk in risks:
        assert "risk_type" in risk
        assert "severity" in risk
        assert "description" in risk
        assert "mitigation" in risk


def test_dataframe_mode_forecast():
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    forecast = result["revenue_forecast"]
    print(f"Forecast: {forecast}")
    assert forecast["projected_revenue"] > 0
    assert forecast["confidence"] in {"Very Low", "Low", "Medium", "High"}
    assert "method" in forecast
    assert "assumptions" in forecast


def test_dataframe_mode_executive_summary():
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    summary = result["executive_financial_summary"]
    print(f"Executive Summary ({len(summary)} items): {summary[:2]}")
    assert len(summary) >= 3
    assert any("revenue" in s.lower() for s in summary)


def test_dataframe_mode_profitability_observations():
    df = _make_mock_df()
    result = estimate_financial_impact(df)
    obs = result["profitability_observations"]
    print(f"Profitability Observations ({len(obs)}): {obs}")
    assert len(obs) >= 2
    assert any("revenue driver" in o.lower() for o in obs)


# ------------------------------------------------------------------ #
# Dictionary mode tests                                               #
# ------------------------------------------------------------------ #

def test_dict_mode_structure():
    """Verify all required top-level keys are present in dictionary mode."""
    insights = _make_mock_sales_insights()
    result = estimate_financial_impact(insights)
    required_keys = {
        "revenue_health",
        "financial_kpis",
        "financial_risks",
        "profitability_observations",
        "revenue_forecast",
        "executive_financial_summary",
    }
    assert required_keys == set(result.keys())


def test_dict_mode_kpis_match_input():
    insights = _make_mock_sales_insights()
    result = estimate_financial_impact(insights)
    kpis = result["financial_kpis"]
    print(f"Dict mode KPIs: {kpis}")
    assert kpis["total_revenue"] == 17500.0
    assert kpis["total_orders"] == 10
    assert kpis["average_order_value"] == 1750.0


def test_dict_mode_revenue_health_growing():
    """mock insights: Jan=5200, Feb=12000, Mar=300.
    first-half = [5200], avg=5200; second-half = [12000, 300], avg=6150.
    Change = +18.3% → Growing.
    """
    insights = _make_mock_sales_insights()
    result = estimate_financial_impact(insights)
    status = result["revenue_health"]["status"]
    print(f"Dict mode revenue health: {status}")
    assert status == "Growing"



def test_dict_mode_risks_detected():
    insights = _make_mock_sales_insights()
    result = estimate_financial_impact(insights)
    risk_types = [r["risk_type"] for r in result["financial_risks"]]
    print(f"Dict mode risks: {risk_types}")
    # PROD_A = 11000 / 17500 = 62.9% → Critical Product Concentration
    assert any("Product Concentration" in rt for rt in risk_types)
    # USA = 15000 / 17500 = 85.7% → Critical Geographic Concentration
    assert any("Geographic Concentration" in rt for rt in risk_types)
    # Cancelled = 2 / 10 = 20% → High Revenue Leakage
    assert any("Leakage" in rt for rt in risk_types)


def test_dict_mode_forecast():
    insights = _make_mock_sales_insights()
    result = estimate_financial_impact(insights)
    forecast = result["revenue_forecast"]
    # trend: Jan=5200, Feb=12000, Mar=300 → WMA = (5200*1 + 12000*2 + 300*3) / 6 = 4966.67
    expected = round((5200 * 1 + 12000 * 2 + 300 * 3) / 6, 2)
    print(f"Dict mode forecast: projected={forecast['projected_revenue']} expected={expected}")
    assert forecast["projected_revenue"] == expected


def test_dict_mode_no_crash_empty_insights():
    """An empty dict should not crash and should return a valid structure."""
    result = estimate_financial_impact({})
    assert "revenue_health" in result
    assert "financial_kpis" in result
    assert "revenue_forecast" in result
    assert result["revenue_forecast"]["confidence"] == "Very Low"
    print("Empty dict mode: handled gracefully.")


def test_dict_mode_with_dataframe_kwarg():
    """When dict is passed alongside df kwarg, KPI enrichment should use the DataFrame."""
    insights = _make_mock_sales_insights()
    df = _make_mock_df()
    result = estimate_financial_impact(insights, df=df)
    kpis = result["financial_kpis"]
    print(f"Dict+df kwarg KPIs: {kpis}")
    # average_items_per_order should be present because df is available
    assert "average_items_per_order" in kpis


# ------------------------------------------------------------------ #
# Test runner                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    tests = [
        # Helper unit tests
        test_revenue_health_growing,
        test_revenue_health_declining,
        test_revenue_health_stable,
        test_revenue_health_single_period,
        test_revenue_health_empty,
        # Forecast
        test_forecast_three_periods,
        test_forecast_six_periods,
        test_forecast_two_periods,
        test_forecast_one_period,
        test_forecast_empty,
        # DataFrame mode
        test_dataframe_mode_structure,
        test_dataframe_mode_kpis,
        test_dataframe_mode_risks,
        test_dataframe_mode_forecast,
        test_dataframe_mode_executive_summary,
        test_dataframe_mode_profitability_observations,
        # Dictionary mode
        test_dict_mode_structure,
        test_dict_mode_kpis_match_input,
        test_dict_mode_revenue_health_growing,
        test_dict_mode_risks_detected,
        test_dict_mode_forecast,
        test_dict_mode_no_crash_empty_insights,
        test_dict_mode_with_dataframe_kwarg,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS  {test_fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {test_fn.__name__}: {exc}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.")
    if failed:
        raise SystemExit(1)
