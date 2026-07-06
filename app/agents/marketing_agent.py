"""Marketing analysis and recommendation agent for ExecMind AI.

Performs deterministic, rule-based marketing strategy evaluations using 
sales metrics, transaction co-occurrences, and geographical details.
"""

import os
import itertools
from collections import Counter
from typing import Dict, Any, List
import pandas as pd


def _find_column(df: pd.DataFrame, patterns: List[str], default: str = None) -> str:
    """Find a column in a DataFrame matching a list of case-insensitive patterns."""
    cols_clean = [str(c).lower().replace(" ", "").replace("_", "") for c in df.columns]
    for pattern in patterns:
        pattern_clean = pattern.lower().replace(" ", "").replace("_", "")
        if pattern_clean in cols_clean:
            idx = cols_clean.index(pattern_clean)
            return df.columns[idx]
    return default


def recommend_marketing(insights: Any, *args, **kwargs) -> Dict[str, Any]:
    """Generate structured marketing recommendations and insights.
    
    Args:
        insights: Either a pandas DataFrame containing raw sales records,
                  or a dictionary of sales insights.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
        
    Returns:
        A structured dictionary of marketing insights.
    """
    from app.agents.sales_agent import analyze_sales
    
    df = None
    sales_insights = {}
    
    # 1. Resolve inputs
    if isinstance(insights, pd.DataFrame):
        df = insights
        try:
            sales_insights = analyze_sales(df)
        except Exception:
            sales_insights = {}
    elif isinstance(insights, dict):
        sales_insights = insights
        # Attempt to extract raw DataFrame from kwargs or args
        df = kwargs.get("data") or kwargs.get("df")
        if df is None:
            for arg in args:
                if isinstance(arg, pd.DataFrame):
                    df = arg
                    break
                    
    # 2. Extract columns if DataFrame is available
    sales_col, product_col, order_col = None, None, None
    underperforming_products = {}
    cross_sells = []
    
    if df is not None:
        sales_col = _find_column(df, ["sales", "revenue", "total", "amount", "price_each", "priceeach", "turnover"])
        product_col = _find_column(df, ["productcode", "product", "product_code", "item", "product_name", "description", "item_code"])
        order_col = _find_column(df, ["ordernumber", "orderid", "id", "order_number", "invoice", "invoiceno", "order_no", "orderno"])
        
        # Calculate underperforming products (bottom 5 by revenue)
        if sales_col and product_col:
            try:
                numeric_sales = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
                temp_df = df.copy()
                temp_df[sales_col] = numeric_sales
                prod_sales = temp_df.groupby(product_col)[sales_col].sum()
                underperforming_products = prod_sales.sort_values(ascending=True).head(5).round(2).to_dict()
            except Exception:
                underperforming_products = {}
                
        # Mine co-occurrence pairs for cross-selling
        if order_col and product_col:
            try:
                order_groups = df.groupby(order_col)[product_col].apply(set)
                pair_counts = Counter()
                for products in order_groups:
                    if len(products) > 1:
                        # Sort list of products to keep combination tuples sorted
                        sorted_prods = sorted([str(p) for p in products])
                        for p1, p2 in itertools.combinations(sorted_prods, 2):
                            pair_counts[(p1, p2)] += 1
                            
                top_pairs = pair_counts.most_common(3)
                for (p1, p2), count in top_pairs:
                    cross_sells.append({
                        "product_1": p1,
                        "product_2": p2,
                        "co_occurrences": int(count),
                        "recommendation": f"Recommend '{p1}' during checkout when a customer adds '{p2}' to their basket.",
                        "type": "Mined Association"
                    })
            except Exception:
                pass

    # Fallback for Cross-Sells if none found or df is missing
    if not cross_sells:
        top_prods = list(sales_insights.get("top_products_by_revenue", {}).keys())
        if len(top_prods) >= 2:
            cross_sells.append({
                "product_1": top_prods[0],
                "product_2": top_prods[1],
                "co_occurrences": 0,
                "recommendation": f"Bundle top-sellers '{top_prods[0]}' and '{top_prods[1]}' together with a 5% bundle discount.",
                "type": "Top-Seller Bundle"
            })
            
    # 3. Suggested Promotions
    promotions = []
    if underperforming_products:
        worst_prod = list(underperforming_products.keys())[0]
        promotions.append({
            "campaign_type": "Inventory Clearance",
            "target": worst_prod,
            "promotion_detail": f"Offer a 20% discount on '{worst_prod}' to stimulate demand and clear inventory.",
            "rationale": "This product has the lowest recorded sales revenue."
        })
        
    aov = sales_insights.get("average_order_value", 0)
    if aov > 0:
        target_aov = round(aov * 1.15, 2)
        promotions.append({
            "campaign_type": "Average Order Value Boost",
            "target": "All Products",
            "promotion_detail": f"Introduce a volume-based discount: 'Spend ${target_aov:,.2f} or more and get 10% off your entire order'.",
            "rationale": f"Designed to lift the current average order value of ${aov:,.2f}."
        })
        
    status_summary = sales_insights.get("order_status_summary", {})
    cancelled_count = status_summary.get("Cancelled", 0) or status_summary.get("cancelled", 0) or 0
    if cancelled_count > 0:
        promotions.append({
            "campaign_type": "Customer Win-Back",
            "target": "Cancelled Orders",
            "promotion_detail": "Send a targeted re-engagement email to customers with cancelled orders offering free shipping and a $10 coupon.",
            "rationale": f"Found {cancelled_count} cancelled transactions in the order status log."
        })
        
    # 4. Seasonal / Monthly Campaign Recommendations
    monthly_campaigns = []
    monthly_trend = sales_insights.get("monthly_sales_trend", {})
    if monthly_trend:
        peak_month = max(monthly_trend, key=monthly_trend.get)
        trough_month = min(monthly_trend, key=monthly_trend.get)
        
        monthly_campaigns.append({
            "period": peak_month,
            "campaign_name": "Peak Demand Capitalization",
            "strategy": f"Run high-impact loyalty rewards and paid advertising campaigns during the peak month of {peak_month} to maximize customer conversion."
        })
        monthly_campaigns.append({
            "period": trough_month,
            "campaign_name": "Off-Season Demand Stimulus",
            "strategy": f"Launch flash sales, early-bird promotions, or subscriber-only coupon drops in {trough_month} to smooth the cash flow curve."
        })
    else:
        monthly_campaigns.extend([
            {
                "period": "Q4 (Holiday Season)",
                "campaign_name": "Holiday Gifting Campaign",
                "strategy": "Design seasonal gift bundles, corporate bulk gifting discounts, and holiday countdown promotions."
            },
            {
                "period": "Q3 (Off-Peak Period)",
                "campaign_name": "Late Summer Clearance",
                "strategy": "Run a catalogue-wide clearance event to free up capital and prepare warehouse shelf space for the high-demand holiday season."
            }
        ])
        
    # 5. Market Expansion Opportunities
    market_expansion = []
    top_countries = sales_insights.get("top_countries_by_revenue", {})
    if top_countries:
        top_country = list(top_countries.keys())[0]
        lowest_country = list(top_countries.keys())[-1]
        
        if top_country != lowest_country:
            market_expansion.append({
                "market": lowest_country,
                "strategy": f"Expand marketing presence in '{lowest_country}' through localized social media ads and search engine optimization.",
                "priority": "Medium",
                "potential": "Low penetration, high room for growth compared to market leader."
            })
        market_expansion.append({
            "market": f"Regions bordering '{top_country}'",
            "strategy": f"Leverage brand awareness in '{top_country}' to expand into adjacent regional markets.",
            "priority": "High",
            "potential": "High brand affinity spillover."
        })
    else:
        market_expansion.append({
            "market": "Secondary Geographical Demographics",
            "strategy": "Initiate target audience profiling and localized search engine ads in secondary geographical zones.",
            "priority": "Medium",
            "potential": "Untapped regional traffic."
        })
        
    # 6. Marketing Risks
    marketing_risks = []
    total_sales = sales_insights.get("total_sales", 0)
    
    top_products = sales_insights.get("top_products_by_revenue", {})
    if top_products and total_sales > 0:
        top_prod = list(top_products.keys())[0]
        top_prod_rev = list(top_products.values())[0]
        prod_pct = (top_prod_rev / total_sales) * 100
        if prod_pct > 30:
            marketing_risks.append({
                "risk_type": "High Product Concentration",
                "description": f"Over-reliance on '{top_prod}', which represents {prod_pct:.1f}% of total revenue.",
                "mitigation": "Diversify marketing budget allocation to showcase other catalog lines."
            })
            
    if top_countries and total_sales > 0:
        top_country = list(top_countries.keys())[0]
        top_country_rev = list(top_countries.values())[0]
        country_pct = (top_country_rev / total_sales) * 100
        if country_pct > 50:
            marketing_risks.append({
                "risk_type": "High Geographical Concentration",
                "description": f"Over-reliance on the '{top_country}' market, contributing {country_pct:.1f}% of total turnover.",
                "mitigation": "Invest in secondary regional campaigns to hedge against localized economic contractions."
            })
            
    total_records = sum(status_summary.values()) if status_summary else 0
    if total_records > 0 and cancelled_count > 0:
        cancelled_pct = (cancelled_count / total_records) * 100
        if cancelled_pct > 5:
            marketing_risks.append({
                "risk_type": "High Transaction Cancellation",
                "description": f"Cancelled transactions represent {cancelled_pct:.1f}% of all log entries.",
                "mitigation": "Audit post-purchase email follow-ups, customer confirmation prompts, and payment gateway friction points."
            })
            
    if not marketing_risks:
        marketing_risks.append({
            "risk_type": "Low Concentration Risk",
            "description": "No major structural exposure or concentration anomalies detected in channels.",
            "mitigation": "Maintain standard advertising budget distributions."
        })
        
    # 7. Key Marketing Observations
    observations = []
    if underperforming_products:
        worst_prod = list(underperforming_products.keys())[0]
        observations.append(
            f"Product support warning: '{worst_prod}' has the lowest revenue contribution "
            f"and requires target promotion support."
        )
        
    if cross_sells:
        best_pair = cross_sells[0]
        if best_pair.get("co_occurrences", 0) > 0:
            observations.append(
                f"Strong basket affinity found between '{best_pair['product_1']}' and "
                f"'{best_pair['product_2']}' ({best_pair['co_occurrences']} order co-occurrences). Create checkout upsell flows."
            )
        else:
            observations.append(
                f"Product bundle potential: Recommend bundling '{best_pair['product_1']}' and "
                f"'{best_pair['product_2']}' to capture higher basket value."
            )
            
    if marketing_risks:
        concentration_risks = [r for r in marketing_risks if "Concentration" in r["risk_type"]]
        if concentration_risks:
            observations.append(
                f"Diversification alert: {concentration_risks[0]['description']}. Restructure ad campaigns to limit exposure."
            )
            
    observations.append("Introduce off-season campaign schedules to stabilize seasonal cash flow cycles.")
    
    return {
        "underperforming_products": underperforming_products,
        "suggested_promotions": promotions,
        "cross_sell_opportunities": cross_sells,
        "seasonal_campaign_recommendations": monthly_campaigns,
        "market_expansion_opportunities": market_expansion,
        "marketing_risks": marketing_risks,
        "key_marketing_observations": observations
    }

