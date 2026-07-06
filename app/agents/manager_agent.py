"""Manager agent for ExecMind AI.

Orchestrates the analysis pipeline by coordinating the specialist agents
(Sales, Marketing, and Finance) and synthesizing their outputs into a single
cohesive Executive Business Report.
"""

from typing import Dict, Any, List
import pandas as pd

from app.agents.sales_agent import analyze_sales
from app.agents.marketing_agent import recommend_marketing
from app.agents.finance_agent import estimate_financial_impact


def _clamp_score(score: float) -> int:
    """Clamp a raw score into the inclusive 0-100 range."""
    return max(0, min(100, int(round(score))))


def _severity_penalty(severity: str) -> int:
    """Map a severity label to a score penalty."""
    severity_value = str(severity).lower()
    if severity_value == "high":
        return 12
    if severity_value == "medium":
        return 6
    if severity_value == "low":
        return 2
    return 0


def _domain_risk_penalty(risks: List[Dict[str, Any]]) -> int:
    """Compute the penalty from a list of risk dictionaries."""
    return sum(_severity_penalty(risk.get("severity", "")) for risk in risks)


def _calculate_business_health_score(
    revenue_status: str,
    sales_insights: Dict[str, Any],
    marketing_insights: Dict[str, Any],
    finance_insights: Dict[str, Any],
    overall_risks: List[Dict[str, Any]],
) -> int:
    """Convert core business KPIs into a 0-100 executive health score.

    The score blends four domains already present in the report:
    financial trend/volatility, sales concentration, marketing risks/opportunities,
    and the consolidated risk register. Each domain is normalized to a 0-100
    score and then combined with fixed weights.
    """

    financial_kpis = finance_insights.get("financial_kpis", {})
    finance_risks = finance_insights.get("financial_risks", [])
    marketing_risks = marketing_insights.get("marketing_risks", [])
    promotional_signals = marketing_insights.get("suggested_promotions", [])
    cross_sell_signals = marketing_insights.get("cross_sell_opportunities", [])
    market_expansion_signals = marketing_insights.get("market_expansion_opportunities", [])

    # Financial score: trend plus volatility, then penalize detected financial risks.
    financial_score = 82.0
    if revenue_status == "Growing":
        financial_score += 10
    elif revenue_status == "Stable":
        financial_score += 2
    else:
        financial_score -= 14

    volatility = float(financial_kpis.get("monthly_revenue_volatility_pct", 0.0) or 0.0)
    if volatility > 60:
        financial_score -= 18
    elif volatility > 35:
        financial_score -= 10
    elif volatility > 15:
        financial_score -= 4

    financial_score -= _domain_risk_penalty(finance_risks)
    if not finance_risks:
        financial_score += 4

    # Sales score: reward diversified revenue and penalize concentration.
    total_sales = float(sales_insights.get("total_sales", 0.0) or 0.0)
    sales_score = 78.0 if total_sales > 0 else 0.0
    if total_sales > 0:
        top_products = sales_insights.get("top_products_by_revenue", {})
        if top_products:
            top_product_revenue = float(list(top_products.values())[0] or 0.0)
            top_product_share = top_product_revenue / total_sales * 100
            if top_product_share > 50:
                sales_score -= 20
            elif top_product_share > 30:
                sales_score -= 12
            elif top_product_share > 20:
                sales_score -= 5
            else:
                sales_score += 4

        top_countries = sales_insights.get("top_countries_by_revenue", {})
        if top_countries:
            top_country_revenue = float(list(top_countries.values())[0] or 0.0)
            top_country_share = top_country_revenue / total_sales * 100
            if top_country_share > 70:
                sales_score -= 18
            elif top_country_share > 50:
                sales_score -= 10
            elif top_country_share > 35:
                sales_score -= 4
            else:
                sales_score += 3

        if total_sales >= 10000:
            sales_score += 4

    # Marketing score: reflect existing promotion, cross-sell, and expansion signals
    # while still penalizing visible marketing risks.
    marketing_score = 80.0
    marketing_score -= _domain_risk_penalty(marketing_risks)
    marketing_score += min(6, len(promotional_signals) * 2)
    marketing_score += min(4, len(cross_sell_signals) * 2)
    marketing_score += min(3, len(market_expansion_signals))
    if not marketing_risks:
        marketing_score += 4

    # Consolidated risk score: uses the final risk register to capture the overall
    # business exposure after the specialist analyses are merged.
    risk_score = 92.0
    for risk in overall_risks:
        risk_score -= _severity_penalty(risk.get("severity", ""))
    if len(overall_risks) >= 4:
        risk_score -= 6
    elif len(overall_risks) == 3:
        risk_score -= 3
    elif len(overall_risks) == 2:
        risk_score -= 1
    if overall_risks and overall_risks[0].get("risk_type") == "No Critical Risks Detected":
        risk_score += 3

    weighted_score = (
        financial_score * 0.35
        + sales_score * 0.30
        + marketing_score * 0.20
        + risk_score * 0.15
    )

    return _clamp_score(weighted_score)


def build_report(data: pd.DataFrame, *args, **kwargs) -> Dict[str, Any]:
    """Coordinatively execute Sales, Marketing, and Finance analyses.

    Produces a unified Executive Business Report.

    Args:
        data: A pandas DataFrame containing transactional sales records.
        *args: Optional positional arguments passed to downstream agents.
        **kwargs: Optional keyword arguments passed to downstream agents.

    Returns:
        A structured dictionary representing the unified Executive Business Report.

    Raises:
        ValueError: If input data is None, not a DataFrame, or empty.
    """
    # 1. Validate non-empty input
    if data is None:
        raise ValueError("Input data cannot be None.")
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("Input data DataFrame is empty.")

    # 2. Call Sales Agent exactly once
    sales_insights = analyze_sales(data, *args, **kwargs)

    # 3. Pass Sales insights directly to Marketing and Finance Agents
    # Avoid duplicate Sales calculations by utilizing their dual-input interface,
    # passing the DataFrame as an optional parameter for additional metrics.
    marketing_insights = recommend_marketing(sales_insights, df=data, *args, **kwargs)
    finance_insights = estimate_financial_impact(sales_insights, df=data, *args, **kwargs)

    # 4. Determine Overall Business Risks
    overall_risks = []
    
    # Process Finance risks
    for risk in finance_insights.get("financial_risks", []):
        if risk.get("risk_type") != "No Significant Financial Risks Detected":
            overall_risks.append({
                "risk_type": risk.get("risk_type"),
                "severity": risk.get("severity", "Medium"),
                "source": "Finance",
                "description": risk.get("description"),
                "mitigation": risk.get("mitigation")
            })
            
    # Process Marketing risks
    for risk in marketing_insights.get("marketing_risks", []):
        if risk.get("risk_type") != "Low Concentration Risk":
            overall_risks.append({
                "risk_type": risk.get("risk_type"),
                "severity": "Medium",
                "source": "Marketing",
                "description": risk.get("description"),
                "mitigation": risk.get("mitigation")
            })


    if not overall_risks:
        overall_risks.append({
            "risk_type": "No Critical Risks Detected",
            "severity": "Low",
            "source": "System",
            "description": "No significant financial or marketing risks detected in the dataset.",
            "mitigation": "Continue standard operations and monitor performance quarterly."
        })

    # 5. Determine Overall Business Health (Healthy / Moderate / Critical)
    revenue_status = finance_insights.get("revenue_health", {}).get("status", "Stable")
    high_risks = [r for r in overall_risks if r.get("severity") == "High"]
    medium_risks = [r for r in overall_risks if r.get("severity") == "Medium"]
    business_health_score = _calculate_business_health_score(
        revenue_status,
        sales_insights,
        marketing_insights,
        finance_insights,
        overall_risks,
    )

    if (len(high_risks) >= 1 and revenue_status == "Declining") or len(high_risks) >= 2:
        business_health = "Critical"
    elif revenue_status == "Declining" or len(high_risks) >= 1 or len(medium_risks) >= 2:
        business_health = "Moderate"
    else:
        business_health = "Healthy"

    # 6. Generate Top Priorities (3-5 items)
    priorities = []
    
    # Priority 1: High severity risks mitigation
    for r in high_risks[:2]:
        priorities.append(f"Mitigate high-severity risk: {r.get('description')} Action: {r.get('mitigation')}")
        
    # Priority 2: Decline reversal if applicable
    if revenue_status == "Declining" and len(priorities) < 5:
        priorities.append("Address contracting sales: Restructure off-season marketing cycles to stabilize revenue.")
        
    # Priority 3: Suggested Promotion
    promotions = marketing_insights.get("suggested_promotions", [])
    if promotions and len(priorities) < 5:
        first_promo = promotions[0]
        priorities.append(
            f"Launch marketing campaign ({first_promo.get('campaign_type')}): "
            f"{first_promo.get('promotion_detail')}"
        )
        
    # Priority 4: Cross-sell implementation
    cross_sells = marketing_insights.get("cross_sell_opportunities", [])
    if cross_sells and len(priorities) < 5:
        first_cross = cross_sells[0]
        if first_cross.get("co_occurrences", 0) > 0:
            priorities.append(
                f"Deploy checkout bundle: Offer '{first_cross.get('product_1')}' and "
                f"'{first_cross.get('product_2')}' together to capture proven basket affinity."
            )
        else:
            priorities.append(
                f"Introduce product grouping: Bundle top sellers '{first_cross.get('product_1')}' "
                f"and '{first_cross.get('product_2')}' to raise average order value."
            )

    # Pad if priorities < 3
    if len(priorities) < 3:
        top_products = sales_insights.get("top_products_by_revenue", {})
        if top_products:
            top_prod = list(top_products.keys())[0]
            priorities.append(f"Ensure supply chain stability for primary product: '{top_prod}'.")
    if len(priorities) < 3:
        priorities.append("Establish a continuous dashboard monitoring customer retention and unit economics.")
    if len(priorities) < 3:
        priorities.append("Evaluate pricing model flexibility across primary regional corridors.")

    # Slice to keep between 3 and 5 items
    priorities = priorities[:5]

    # 7. Recommended Next Steps (tactical actions)
    next_steps = [
        "Convene leadership alignment meeting to distribute ownership of the Top Priorities.",
        "Perform a comprehensive inventory and logistics review for top-performing SKUs."
    ]
    
    # Check for cancellation leakage to offer specific next step
    has_leakage = any("leakage" in r.get("risk_type", "").lower() or "cancellation" in r.get("risk_type", "").lower() for r in overall_risks)
    if has_leakage:
        next_steps.append("Audit payment gateways and post-checkout customer touchpoints to minimize cancellation leakage.")
    else:
        next_steps.append("Schedule a secondary marketing performance review to monitor cross-selling adoption.")

    next_steps.append("Initiate monthly reporting schedules in ExecMind to evaluate the revenue forecast accuracy.")

    # 8. Executive Summary Synthesized
    total_sales = sales_insights.get("total_sales", 0.0)
    total_orders = sales_insights.get("total_orders", 0)
    aov = sales_insights.get("average_order_value", 0.0)
    top_country = list(sales_insights.get("top_countries_by_revenue", {}).keys())[0] if sales_insights.get("top_countries_by_revenue") else "N/A"
    
    exec_summary = [
        f"ExecMind autonomous analysis completed. Business Health is assessed as {business_health}.",
        f"Total revenue generated: ${total_sales:,.2f} across {total_orders:,} orders, averaging ${aov:,.2f} per transaction.",
        f"Primary regional market: '{top_country}' remains the leading geographic revenue generator.",
        f"Revenue trend is currently evaluated as {revenue_status}. A total of {len(overall_risks)} overall business risk factors were detected."
    ]

    return {
        "executive_summary": exec_summary,
        "business_health": business_health,
        "sales_insights": {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "average_order_value": aov,
            "monthly_sales_trend": sales_insights.get("monthly_sales_trend", {}),
            "top_products_by_revenue": sales_insights.get("top_products_by_revenue", {}),
            "top_countries_by_revenue": sales_insights.get("top_countries_by_revenue", {}),
            "key_observations": sales_insights.get("key_observations", [])
        },
        "marketing_recommendations": {
            "suggested_promotions": marketing_insights.get("suggested_promotions", []),
            "cross_sell_opportunities": marketing_insights.get("cross_sell_opportunities", []),
            "seasonal_campaign_recommendations": marketing_insights.get("seasonal_campaign_recommendations", []),
            "market_expansion_opportunities": marketing_insights.get("market_expansion_opportunities", []),
            "key_marketing_observations": marketing_insights.get("key_marketing_observations", [])
        },
        "financial_assessment": {
            "revenue_health": finance_insights.get("revenue_health", {}),
            "financial_kpis": finance_insights.get("financial_kpis", {}),
            "profitability_observations": finance_insights.get("profitability_observations", []),
            "revenue_forecast": finance_insights.get("revenue_forecast", {}),
            "business_health_score": business_health_score,
            "executive_financial_summary": finance_insights.get("executive_financial_summary", [])
        },
        "overall_risks": overall_risks,
        "top_priorities": priorities,
        "recommended_next_steps": next_steps
    }
