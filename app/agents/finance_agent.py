"""Finance impact and profitability analysis agent for ExecMind AI.

Performs deterministic financial analysis including revenue health assessment,
KPI extraction, risk identification, profitability observations, simple trend-based
forecasting, and executive financial summary generation.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def _find_column(df: pd.DataFrame, patterns: List[str], default: Optional[str] = None) -> Optional[str]:
    """Find a column in a DataFrame matching a list of case-insensitive patterns.

    Args:
        df: The source DataFrame to search.
        patterns: Ordered list of candidate column name patterns to try.
        default: Value to return when no match is found.

    Returns:
        The matched column name, or ``default`` if no match is found.
    """
    cols_clean = [str(c).lower().replace(" ", "").replace("_", "") for c in df.columns]
    for pattern in patterns:
        pattern_clean = pattern.lower().replace(" ", "").replace("_", "")
        if pattern_clean in cols_clean:
            idx = cols_clean.index(pattern_clean)
            return df.columns[idx]
    return default


def _assess_revenue_health(monthly_trend: Dict[str, float]) -> Tuple[str, str]:
    """Assess overall revenue health trend from the monthly sales series.

    Args:
        monthly_trend: Ordered dict mapping period strings (e.g. '2026-01') to revenue floats.

    Returns:
        A tuple of (status, explanation) where status is one of
        'Growing', 'Stable', or 'Declining'.
    """
    if not monthly_trend or len(monthly_trend) < 2:
        return (
            "Stable",
            "Insufficient historical data points to determine a directional trend. "
            "A minimum of two periods is required for comparison.",
        )

    values = list(monthly_trend.values())
    first_half_avg = sum(values[: len(values) // 2]) / max(len(values) // 2, 1)
    second_half_avg = sum(values[len(values) // 2 :]) / max(len(values) - len(values) // 2, 1)

    change_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0.0

    if change_pct >= 5:
        status = "Growing"
        explanation = (
            f"Revenue is accelerating. The second half of recorded periods averages "
            f"${second_half_avg:,.2f}, up {change_pct:.1f}% from the first-half average "
            f"of ${first_half_avg:,.2f}."
        )
    elif change_pct <= -5:
        status = "Declining"
        explanation = (
            f"Revenue is contracting. The second half of recorded periods averages "
            f"${second_half_avg:,.2f}, down {abs(change_pct):.1f}% from the first-half "
            f"average of ${first_half_avg:,.2f}."
        )
    else:
        status = "Stable"
        explanation = (
            f"Revenue is broadly stable, with a marginal {change_pct:+.1f}% variance "
            f"between the first-half average (${first_half_avg:,.2f}) and the second-half "
            f"average (${second_half_avg:,.2f})."
        )

    return status, explanation


def _generate_forecast(monthly_trend: Dict[str, float]) -> Dict[str, Any]:
    """Generate a simple deterministic revenue forecast for the next period.

    Uses a 3-period weighted moving average (most recent period carries the
    highest weight) when enough data is available, otherwise falls back to a
    simple trailing average.

    Args:
        monthly_trend: Ordered dict mapping period strings to revenue floats.

    Returns:
        A dict with keys: projected_revenue, confidence, method, assumptions.
    """
    if not monthly_trend:
        return {
            "projected_revenue": 0.0,
            "confidence": "Very Low",
            "method": "No Data",
            "assumptions": "No monthly trend data is available to generate a forecast.",
        }

    values = list(monthly_trend.values())
    n = len(values)

    if n >= 3:
        # Weighted moving average: weights [1, 2, 3] for last three periods
        recent = values[-3:]
        weights = [1, 2, 3]
        projected = sum(v * w for v, w in zip(recent, weights)) / sum(weights)
        method = "3-Period Weighted Moving Average (weights 1:2:3)"
        confidence = "Medium" if n >= 6 else "Low"
        assumptions = (
            "Assumes no major external demand shocks. Based on the last three recorded "
            f"periods ({', '.join(list(monthly_trend.keys())[-3:])})."
        )
    elif n == 2:
        projected = (values[-1] * 2 + values[-2]) / 3
        method = "2-Period Weighted Average"
        confidence = "Low"
        assumptions = "Forecast based on only two periods; treat as directional guidance only."
    else:
        projected = values[0]
        method = "Single Period Carry-Forward"
        confidence = "Very Low"
        assumptions = "Only one data point available. Forecast carries forward the single recorded period."

    return {
        "projected_revenue": round(projected, 2),
        "confidence": confidence,
        "method": method,
        "assumptions": assumptions,
    }


def _compute_financial_kpis(
    sales_insights: Dict[str, Any],
    df: Optional[pd.DataFrame],
    sales_col: Optional[str],
    order_col: Optional[str],
    quantity_col: Optional[str],
    customer_col: Optional[str],
) -> Dict[str, Any]:
    """Compute the core financial KPIs from sales insights and optional DataFrame columns.

    Args:
        sales_insights: Pre-computed sales insights dictionary.
        df: Optional raw DataFrame for additional column-level computations.
        sales_col: Resolved sales/revenue column name.
        order_col: Resolved order identifier column name.
        quantity_col: Resolved quantity column name.
        customer_col: Resolved customer identifier column name.

    Returns:
        A dictionary of named financial KPIs.
    """
    total_revenue = sales_insights.get("total_sales", 0.0)
    total_orders = sales_insights.get("total_orders", 0)
    aov = sales_insights.get("average_order_value", 0.0)

    kpis: Dict[str, Any] = {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "average_order_value": round(aov, 2),
        "revenue_per_order": round(aov, 2),
    }

    # Revenue per unique customer
    if df is not None and customer_col and order_col:
        try:
            n_customers = df[customer_col].nunique()
            if n_customers > 0:
                kpis["revenue_per_customer"] = round(total_revenue / n_customers, 2)
                kpis["unique_customers"] = int(n_customers)
        except Exception:
            pass

    # Average quantity per order
    if df is not None and quantity_col and order_col:
        try:
            numeric_qty = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)
            avg_qty = float(numeric_qty.sum() / max(total_orders, 1))
            kpis["average_items_per_order"] = round(avg_qty, 2)
        except Exception:
            pass

    # Monthly revenue stats
    monthly_trend = sales_insights.get("monthly_sales_trend", {})
    if monthly_trend:
        values = list(monthly_trend.values())
        kpis["peak_monthly_revenue"] = round(max(values), 2)
        kpis["trough_monthly_revenue"] = round(min(values), 2)
        kpis["monthly_revenue_volatility_pct"] = round(
            (max(values) - min(values)) / max(max(values), 1) * 100, 1
        )

    return kpis


def _detect_financial_risks(
    sales_insights: Dict[str, Any], kpis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect and describe financial concentration and structural risks.

    Args:
        sales_insights: Pre-computed sales insights dictionary.
        kpis: Financial KPIs dictionary produced by :func:`_compute_financial_kpis`.

    Returns:
        A list of risk dictionaries, each with keys:
        risk_type, severity, description, and mitigation.
    """
    risks: List[Dict[str, Any]] = []
    total_revenue = sales_insights.get("total_sales", 0.0)

    # Product concentration risk
    top_products = sales_insights.get("top_products_by_revenue", {})
    if top_products and total_revenue > 0:
        top_prod = list(top_products.keys())[0]
        top_prod_rev = list(top_products.values())[0]
        pct = top_prod_rev / total_revenue * 100
        if pct > 50:
            risks.append({
                "risk_type": "Critical Product Concentration",
                "severity": "High",
                "description": f"'{top_prod}' alone generates {pct:.1f}% of total revenue.",
                "mitigation": "Immediately diversify the product portfolio and invest in adjacent SKU promotions.",
            })
        elif pct > 30:
            risks.append({
                "risk_type": "Elevated Product Concentration",
                "severity": "Medium",
                "description": f"'{top_prod}' accounts for {pct:.1f}% of total revenue.",
                "mitigation": "Gradually expand secondary product lines to reduce single-product dependency.",
            })

    # Geographic concentration risk
    top_countries = sales_insights.get("top_countries_by_revenue", {})
    if top_countries and total_revenue > 0:
        top_country = list(top_countries.keys())[0]
        top_country_rev = list(top_countries.values())[0]
        pct = top_country_rev / total_revenue * 100
        if pct > 70:
            risks.append({
                "risk_type": "Critical Geographic Concentration",
                "severity": "High",
                "description": f"'{top_country}' accounts for {pct:.1f}% of total revenue.",
                "mitigation": "Urgently expand into at least two additional geographic markets.",
            })
        elif pct > 50:
            risks.append({
                "risk_type": "Elevated Geographic Concentration",
                "severity": "Medium",
                "description": f"'{top_country}' contributes {pct:.1f}% of total revenue.",
                "mitigation": "Increase marketing spend in secondary markets to reduce regional dependency.",
            })

    # Cancellation / revenue leakage risk
    status_summary = sales_insights.get("order_status_summary", {})
    cancelled = status_summary.get("Cancelled", 0) or status_summary.get("cancelled", 0) or 0
    total_records = sum(status_summary.values()) if status_summary else 0
    if total_records > 0 and cancelled > 0:
        cancelled_pct = cancelled / total_records * 100
        if cancelled_pct > 10:
            risks.append({
                "risk_type": "High Revenue Leakage (Cancellations)",
                "severity": "High",
                "description": f"{cancelled_pct:.1f}% of recorded transactions were cancelled.",
                "mitigation": "Investigate root causes — payment failures, stock-outs, or UX friction — and implement targeted retention interventions.",
            })
        elif cancelled_pct > 5:
            risks.append({
                "risk_type": "Moderate Revenue Leakage (Cancellations)",
                "severity": "Medium",
                "description": f"{cancelled_pct:.1f}% of transactions were cancelled.",
                "mitigation": "Introduce post-checkout confirmation flows and targeted email win-back campaigns.",
            })

    # Seasonal volatility risk
    volatility = kpis.get("monthly_revenue_volatility_pct", 0.0)
    if volatility > 60:
        risks.append({
            "risk_type": "High Seasonal Revenue Volatility",
            "severity": "Medium",
            "description": f"Monthly revenue swings by {volatility:.1f}% between peak and trough periods.",
            "mitigation": "Introduce off-peak promotional campaigns and subscription-based revenue models to smooth cash flow.",
        })

    if not risks:
        risks.append({
            "risk_type": "No Significant Financial Risks Detected",
            "severity": "Low",
            "description": "All key financial concentration and leakage metrics are within acceptable thresholds.",
            "mitigation": "Maintain current operational discipline and schedule a quarterly financial review.",
        })

    return risks


def _generate_profitability_observations(
    sales_insights: Dict[str, Any], kpis: Dict[str, Any], revenue_status: str
) -> List[str]:
    """Generate deterministic, business-readable profitability observations.

    Args:
        sales_insights: Pre-computed sales insights dictionary.
        kpis: Financial KPIs dictionary.
        revenue_status: Revenue health status string ('Growing', 'Stable', or 'Declining').

    Returns:
        A list of concise profitability observation strings.
    """
    observations: List[str] = []
    total_revenue = sales_insights.get("total_sales", 0.0)
    total_orders = sales_insights.get("total_orders", 0)

    # Strongest driver
    top_products = sales_insights.get("top_products_by_revenue", {})
    if top_products:
        top_prod = list(top_products.keys())[0]
        top_prod_rev = list(top_products.values())[0]
        top_prod_pct = top_prod_rev / total_revenue * 100 if total_revenue > 0 else 0
        observations.append(
            f"Strongest revenue driver: '{top_prod}' contributes ${top_prod_rev:,.2f} "
            f"({top_prod_pct:.1f}% of total revenue)."
        )

    # Weakest contributor
    if len(top_products) >= 2:
        weak_prod = list(top_products.keys())[-1]
        weak_prod_rev = list(top_products.values())[-1]
        observations.append(
            f"Weakest top-5 product: '{weak_prod}' generates only ${weak_prod_rev:,.2f} — "
            f"a candidate for product review or consolidation."
        )

    # AOV observation
    aov = kpis.get("average_order_value", 0.0)
    if aov > 0:
        observations.append(
            f"Average Order Value is ${aov:,.2f}. A 10% AOV improvement would add "
            f"${total_orders * aov * 0.10:,.2f} to revenue without acquiring new customers."
        )

    # Declining trend warning
    if revenue_status == "Declining":
        trough = kpis.get("trough_monthly_revenue", 0.0)
        observations.append(
            f"Declining revenue trend detected. The lowest recorded monthly revenue "
            f"stands at ${trough:,.2f}. Immediate corrective action is recommended."
        )

    # Seasonal peak / cash-flow note
    monthly_trend = sales_insights.get("monthly_sales_trend", {})
    if monthly_trend:
        peak_month = max(monthly_trend, key=monthly_trend.get)
        trough_month = min(monthly_trend, key=monthly_trend.get)
        if peak_month != trough_month:
            observations.append(
                f"Cash-flow concern: Revenue in the trough month ({trough_month}) is "
                f"${monthly_trend[trough_month]:,.2f}, which is "
                f"{(1 - monthly_trend[trough_month] / monthly_trend[peak_month]) * 100:.1f}% "
                f"lower than the peak ({peak_month}, ${monthly_trend[peak_month]:,.2f}). "
                f"Ensure adequate working capital reserves."
            )

    return observations


def _generate_executive_summary(
    sales_insights: Dict[str, Any],
    kpis: Dict[str, Any],
    revenue_status: str,
    risks: List[Dict[str, Any]],
    forecast: Dict[str, Any],
) -> List[str]:
    """Generate concise bullet-style executive financial summary statements.

    Args:
        sales_insights: Pre-computed sales insights dictionary.
        kpis: Financial KPIs dictionary.
        revenue_status: Revenue health status string.
        risks: List of detected financial risk dictionaries.
        forecast: Revenue forecast dictionary.

    Returns:
        A list of bullet-style executive summary strings.
    """
    summary: List[str] = []

    total_revenue = kpis.get("total_revenue", 0.0)
    total_orders = kpis.get("total_orders", 0)
    aov = kpis.get("average_order_value", 0.0)

    summary.append(
        f"Total revenue stands at ${total_revenue:,.2f} across {total_orders:,} orders "
        f"(AOV: ${aov:,.2f}). Revenue trend is currently {revenue_status}."
    )

    projected = forecast.get("projected_revenue", 0.0)
    confidence = forecast.get("confidence", "Unknown")
    summary.append(
        f"Next-period revenue projection: ${projected:,.2f} "
        f"(Confidence: {confidence}, Method: {forecast.get('method', 'N/A')})."
    )

    high_risks = [r for r in risks if r.get("severity") == "High"]
    if high_risks:
        risk_names = ", ".join(r["risk_type"] for r in high_risks)
        summary.append(f"High-severity financial risks require immediate attention: {risk_names}.")
    else:
        summary.append("No high-severity financial risks detected. Standard monitoring continues.")

    top_countries = sales_insights.get("top_countries_by_revenue", {})
    if top_countries:
        top_country = list(top_countries.keys())[0]
        top_country_rev = list(top_countries.values())[0]
        summary.append(
            f"Geographic revenue leader: '{top_country}' contributes "
            f"${top_country_rev:,.2f} to total revenue."
        )

    top_products = sales_insights.get("top_products_by_revenue", {})
    if top_products:
        top_prod = list(top_products.keys())[0]
        summary.append(
            f"Top revenue product: '{top_prod}' — prioritise stock and fulfilment capacity planning."
        )

    return summary


def estimate_financial_impact(insights: Any, *args, **kwargs) -> Dict[str, Any]:
    """Generate structured financial analysis and executive insights.

    Accepts either a raw pandas DataFrame or a pre-computed sales insights
    dictionary. When a DataFrame is provided, the Sales Agent is called
    internally to produce base metrics, matching the pattern established
    in the Marketing Agent.

    Args:
        insights: A pandas DataFrame containing raw sales records, or a
                  dictionary of pre-computed sales insights.
        *args: Optional positional arguments. A DataFrame passed here will
               be used for column-level KPI enrichment when ``insights``
               is a dict.
        **kwargs: Optional keyword arguments. Supports ``data`` and ``df``
                  keys for passing a DataFrame alongside an insights dict.

    Returns:
        A structured dictionary with the following top-level keys:
        - revenue_health
        - financial_kpis
        - financial_risks
        - profitability_observations
        - revenue_forecast
        - executive_financial_summary
    """
    from app.agents.sales_agent import analyze_sales

    df: Optional[pd.DataFrame] = None
    sales_insights: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # 1. Resolve inputs — identical pattern to the Marketing Agent        #
    # ------------------------------------------------------------------ #
    if isinstance(insights, pd.DataFrame):
        df = insights
        try:
            sales_insights = analyze_sales(df)
        except Exception:
            sales_insights = {}
    elif isinstance(insights, dict):
        sales_insights = insights
        df = kwargs.get("data") or kwargs.get("df")
        if df is None:
            for arg in args:
                if isinstance(arg, pd.DataFrame):
                    df = arg
                    break

    # ------------------------------------------------------------------ #
    # 2. Resolve optional DataFrame columns                               #
    # ------------------------------------------------------------------ #
    sales_col: Optional[str] = None
    order_col: Optional[str] = None
    quantity_col: Optional[str] = None
    customer_col: Optional[str] = None

    if df is not None:
        sales_col = _find_column(df, ["sales", "revenue", "total", "amount", "price_each", "priceeach", "turnover"])
        order_col = _find_column(df, ["ordernumber", "orderid", "id", "order_number", "invoice", "invoiceno", "order_no", "orderno"])
        quantity_col = _find_column(df, ["quantityordered", "quantity", "qty", "units", "quantity_ordered"])
        customer_col = _find_column(df, ["customername", "customer", "client", "customerid", "customer_id", "customer_name"])

    # ------------------------------------------------------------------ #
    # 3. Compute each output section                                      #
    # ------------------------------------------------------------------ #
    monthly_trend = sales_insights.get("monthly_sales_trend", {})

    revenue_status, revenue_explanation = _assess_revenue_health(monthly_trend)

    kpis = _compute_financial_kpis(
        sales_insights, df, sales_col, order_col, quantity_col, customer_col
    )

    risks = _detect_financial_risks(sales_insights, kpis)

    profitability_observations = _generate_profitability_observations(
        sales_insights, kpis, revenue_status
    )

    forecast = _generate_forecast(monthly_trend)

    executive_summary = _generate_executive_summary(
        sales_insights, kpis, revenue_status, risks, forecast
    )

    return {
        "revenue_health": {
            "status": revenue_status,
            "explanation": revenue_explanation,
        },
        "financial_kpis": kpis,
        "financial_risks": risks,
        "profitability_observations": profitability_observations,
        "revenue_forecast": forecast,
        "executive_financial_summary": executive_summary,
    }

